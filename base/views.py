from django.http import response
from django.shortcuts import render, HttpResponse, redirect
import json
from django.db import connection
from taicat.models import Deployment, HomePageStat, Image, Contact, Organization, Project, Species
from django.db.models import Count, Window, F, Sum, Min, Q, Max
from django.db.models.functions import ExtractYear
from django.template import loader
import requests
from django.contrib import messages
import time
import pandas as pd
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.storage import FileSystemStorage
import os
from django.conf import settings
# from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import threading
from django.http import response, JsonResponse
from .models import *
from taicat.utils import get_my_project_list, get_project_member
from django.db.models.functions import Trunc, TruncDate
from .utils import DecimalEncoder
from django.views.decorators.csrf import csrf_exempt


def update_is_read(request):
    if request.method == 'GET':
        if contact_id := request.session['id'] :
            UploadNotification.objects.filter(contact_id=contact_id).update(is_read=True)
    return JsonResponse({'data': 'success'}, safe=False) 


@csrf_exempt
def send_upload_notification(upload_history_id, member_list):
    try:
        email_list = []
        email = Contact.objects.filter(id__in=member_list).values('email')
        for e in email:
            email_list += [e['email']]
        uh = UploadHistory.objects.filter(id=upload_history_id)
        if uh[0].status == 'finished':
            status = '已完成' 
        elif uh[0].status ==  'unfinished':
            status = '未完成' 
        elif uh[0].status ==  'uploading':
            status = '上傳中' 
        # send email
        html_content = f"""
        您好：
        <br>
        <br>
        以下為系統上傳活動的通知
        <br>
        <br>
        <b>計畫：</b>{uh[0].deployment_journal.project.name}
        <br>
        <br>
        <b>樣區：</b>{uh[0].deployment_journal.studyarea.name}
        <br>
        <br>
        <b>相機位置：</b>{uh[0].deployment_journal.deployment.name}
        <br>
        <br>
        <b>資料夾名稱：</b>{uh[0].deployment_journal.folder_name}
        <br>
        <br>
        <b>上傳狀態：</b>{status}
        <br>

        """
        subject = '[臺灣自動相機資訊系統] 上傳通知'

        msg = EmailMessage(subject, html_content, 'Camera Trap <no-reply@camera-trap.tw>', [], email_list)
        msg.content_subtype = "html"  # Main content is now text/html
        # 改成背景執行
        task = threading.Thread(target=send_msg, args=(msg,))
        # task.daemon = True
        task.start()
        return {"status": 'success'}
    except:
        return {"status": 'fail'}


@csrf_exempt
def update_upload_history(request):
    # uploading, finished
    response = {}
    if request.method == 'POST':
        client_status = request.POST.get('status')
        deployment_journal_id = request.POST.get('deployment_journal_id')
        if client_status == 'uploading' and deployment_journal_id:
            # 把網頁狀態更新成上傳中
            # 若沒有，新增一個uh
            if uh := UploadHistory.objects.filter(deployment_journal_id=deployment_journal_id).first():
                uh.last_updated = timezone.now()
                uh.status = 'uploading'
                uh.save()
            else: 
                uh = UploadHistory(
                        deployment_journal_id=deployment_journal_id, 
                        status='uploading', 
                        last_updated=timezone.now())
                uh.save()
            response = {'messages': 'success'}
        elif client_status == 'finished' and deployment_journal_id:
            # 判斷網頁狀態是未完成or已完成, species_error & upload_error
            upload_error = True if Image.objects.filter(deployment_journal_id=deployment_journal_id, has_storage='N').exists() else False
            species_error = True if Image.objects.filter(deployment_journal_id=deployment_journal_id, species__in=[None, '']).exists() else False
            status = 'unfinished' if upload_error or species_error else 'finished'
            if uh := UploadHistory.objects.filter(deployment_journal_id=deployment_journal_id).first():
                uh.last_updated = timezone.now()
                uh.status = status
                uh.upload_error = upload_error
                uh.species_error = species_error
                uh.save()
                upload_history_id = UploadHistory.objects.filter(deployment_journal_id=deployment_journal_id)[0].id
            else: 
                uh = UploadHistory(
                        deployment_journal_id=deployment_journal_id, 
                        status=status,
                        upload_error = upload_error,
                        species_error = species_error,
                        last_updated=timezone.now())
                uh.save()
                upload_history_id = uh.id
            if DeploymentJournal.objects.filter(id=deployment_journal_id).exists():
                project_id = DeploymentJournal.objects.filter(id=deployment_journal_id).values('project_id')[0]['project_id']
            else:
                response = {'messages': 'failed due to no associated record in DeploymentJournal table'}
                return JsonResponse(response)
            members = get_project_member(project_id) # 所有計劃下的成員
            final_members = []
            for m in members:
                # 每次都建立新的通知
                try:
                    un = UploadNotification(
                        upload_history_id = upload_history_id,
                        contact_id = m
                    )
                    un.save()
                    final_members += [m]
                except:
                    pass # contact已經不在則移除
            # 每次都寄信
            res = send_upload_notification(upload_history_id,[6])
            if res.get('status') == 'fail':
                response = {'messages': 'failed during sending email'}
                return JsonResponse(response)
            response = {'messages': 'success'}
        else:
            # 回傳沒有結果
            response = {'messages': 'failed due to wrong parameters'}

    return JsonResponse(response)


def get_error_file_list(request, deployment_journal_id):
    data = pd.DataFrame(columns=['所屬計畫', '樣區', '相機位置', '資料夾名稱', '檔名', '錯誤類型'])
    query = """
        SELECT p.name, s.name, d.name, i.folder_name, i.filename, i.species, i.has_storage
        FROM taicat_image i
        JOIN base_uploadhistory up ON i.deployment_journal_id = up.deployment_journal_id
        JOIN taicat_project p ON i.project_id = p.id
        JOIN taicat_deployment d ON i.deployment_id = d.id
        JOIN taicat_studyarea s ON i.studyarea_id = s.id
        WHERE i.deployment_journal_id = {} and (has_storage = 'N' or species is NULL or species = '' )"""
    with connection.cursor() as cursor:
        cursor.execute(query.format(deployment_journal_id))
        data = cursor.fetchall()
        data = pd.DataFrame(data, columns=['所屬計畫', '樣區', '相機位置', '資料夾名稱', '檔名', 'species', 'has_storage'])
        data['錯誤類型'] = ''
        data.loc[data['has_storage']=='N', '錯誤類型'] = '影像未成功上傳'
        data.loc[(data['species'].isin([None, ''])) & (data['has_storage']=='Y'), '錯誤類型'] = data.loc[data['species'].isin([None, '']), '錯誤類型'] + '物種未填寫'
        data.loc[(data['species'].isin([None, ''])) & (data['has_storage']=='N'), '錯誤類型'] = data.loc[data['species'].isin([None, '']), '錯誤類型'] + ', 物種未填寫'
        data = data.drop(columns=['species', 'has_storage'])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="cameratrap_error.xlsx"'
    data.to_excel(response, index=False)
    return response


def upload_history(request):
    rows = []
    if member_id := request.session.get('id', None):
        my_project_list = get_my_project_list(member_id)
        query = """SELECT to_char(up.created AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS'),
                    to_char(up.last_updated AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS'),
                    dj.folder_name, p.name, s.name, d.name, up.status, dj.project_id, up.deployment_journal_id,
                    up.species_error, up.upload_error
                    FROM base_uploadhistory up
                    JOIN taicat_deploymentjournal dj ON up.deployment_journal_id = dj.id
                    JOIN taicat_project p ON dj.project_id = p.id
                    JOIN taicat_deployment d ON dj.deployment_id = d.id
                    JOIN taicat_studyarea s ON dj.studyarea_id = s.id
                    WHERE dj.project_id IN {}"""
        with connection.cursor() as cursor:
            cursor.execute(query.format(str(my_project_list).replace('[','(').replace(']',')')))
            rows = cursor.fetchall()
    return render(request, 'base/upload_history.html', {'rows': rows})


def faq(request):
    return render(request, 'base/faq.html')


def contact_us(request):
    return render(request, 'base/contact_us.html')


def feedback_request(request):
    # print(print(request.POST))
    # https://stackoverflow.com/questions/38345977/filefield-force-using-temporaryuploadedfile
    try:
        # print(request.POST)
        q_detail_type = request.POST.getlist('q-detail-type')
        q_detail_type = ','.join(q_detail_type)
        description = request.POST.get('description')
        email = request.POST.get('email')
        # user = '1'
        user = email.split('@')[0]
        files = request.FILES.getlist('uploaded_file')
        # print(request.FILES.getlist('uploaded_file'))

        # send email
        html_content = f"""
        您好：
        <br>
        <br>
        以下為臺灣自動相機資訊系統收到的問題回饋
        <br>
        <br>
        <b>問題類型：</b>{q_detail_type}
        <br>
        <br>
        <b>問題描述：</b>{description}
        <br>
        <br>
        <b>使用者電子郵件：</b>{email}
        <br>
        """

        subject = '[臺灣自動相機資訊系統] 問題回饋'

        msg = EmailMessage(subject, html_content, 'Camera Trap <no-reply@camera-trap.tw>', [settings.CT_SERVICE_EMAIL])
        msg.content_subtype = "html"  # Main content is now text/html
        # # save files to temporary dir
        for f in files:
            print(f.name)
            fs = FileSystemStorage()
            filename = fs.save(f'email-attachment/{user}_' + f.name, f)
            msg.attach_file(os.path.join('/ct22-volumes/media', filename))

        # 改成背景執行
        task = threading.Thread(target=send_msg, args=(msg,))
        # task.daemon = True
        task.start()

        return JsonResponse({"status": 'success'}, safe=False)
    except:
        return JsonResponse({"status": 'fail'}, safe=False)


def send_msg(msg):
    msg.send()

def policy(request):
    return render(request, 'base/policy.html')


def add_org_admin(request):
    if request.method == 'POST':
        print('hi')
        for i in request.POST:
            print(i)
        redirect(set_permission)


def login_for_test(request):
    next = request.GET.get('next')
    role = request.GET.get('role')
    info = Contact.objects.filter(name=role).values('name', 'id').first()
    request.session["is_login"] = True
    request.session["name"] = role
    request.session["orcid"] = ''
    request.session["id"] = info['id']
    request.session["first_login"] = False

    return redirect(next)


def set_permission(request):
    is_authorized = False
    user_id = request.session.get('id', None)
    # check permission
    # if Contact.objects.filter(id=user_id).filter(Q(is_organization_admin=True) | Q(is_system_admin=True)):
    if Contact.objects.filter(id=user_id).filter(is_system_admin=True):
        is_authorized = True

        if request.method == 'POST':
            type = request.POST.get('type')
            if type == 'add_admin':
                user_id = request.POST.get('user', None)
                org_id = request.POST.get('organization', None)
                if user_id and org_id:
                    Contact.objects.filter(id=user_id).update(is_organization_admin=True, organization_id=org_id)
                    messages.success(request, '新增成功')
            elif type == 'remove_admin':
                user_id = request.POST.get('id', None)
                if user_id:
                    Contact.objects.filter(id=user_id).update(is_organization_admin=False)
                    messages.success(request, '移除成功')
            elif type == 'remove_project':
                relation_id = request.POST.get('id', None)
                if relation_id:
                    Organization.projects.through.objects.filter(id=relation_id).delete()
                    messages.success(request, '移除成功')
            else:
                project_id = request.POST.get('project', None)
                org_id = request.POST.get('organization', None)
                try:
                    Organization.objects.get(id=org_id).projects.add(Project.objects.get(id=project_id))
                    messages.success(request, '新增成功')
                except:
                    messages.error(request, '新增失敗')
        member_list = Contact.objects.all().values('name', 'email', 'id')
        org_list = Organization.objects.all()
        project_list = Project.objects.all().values('name', 'id')

        org_project_list = []
        org_project_set = Organization.projects.through.objects.all()
        for i in org_project_set:
            tmp = {'organization_name': i.organization.name, 'relation_id': i.id,
                   'project_name': i.project.name}
            org_project_list.append(tmp)

        org_admin_list = Contact.objects.filter(is_organization_admin=True).values('organization__name', 'id', 'name', 'email')

        return render(request, 'base/permission.html', {'member_list': member_list, 'org_project_list': org_project_list,
                      'is_authorized': is_authorized, 'org_list': org_list, 'project_list': project_list, 'org_admin_list': org_admin_list})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'base/permission.html', {'is_authorized': is_authorized})


def get_auth_callback(request):
    original_page_url = request.GET.get('next')
    authorization_code = request.GET.get('code')
    data = {'client_id': 'APP-F6POVPAP5L1JOUN1',
            'client_secret': '20acec15-f58b-4653-9695-5e9d2878b673',
            'grant_type': 'authorization_code',
            'code': authorization_code}
    token_url = 'https://orcid.org/oauth/token'

    r = requests.post(token_url, data=data)
    results = r.json()
    orcid = results['orcid']
    name = results['name']

    # check if orcid exists in db
    if Contact.objects.filter(orcid=orcid).exists():
        # if exists, update login status
        info = Contact.objects.filter(orcid=orcid).values('name', 'id').first()
        name = info['name']
        id = info['id']
        request.session["first_login"] = False
    else:
        # if not, create one
        new_user = Contact.objects.create(name=name, orcid=orcid)
        id = new_user.id
        # redirect to set email
        request.session["is_login"] = True
        request.session["name"] = name
        request.session["orcid"] = orcid
        request.session["id"] = id
        request.session["first_login"] = True

        return redirect(personal_info)

    request.session["is_login"] = True
    request.session["name"] = name
    request.session["orcid"] = orcid
    request.session["id"] = id

    return redirect(original_page_url)


def logout(request):
    request.session["is_login"] = False
    request.session["name"] = None
    request.session["orcid"] = None
    request.session["id"] = None
    return redirect('home')


def personal_info(request):
    # login required
    is_login = request.session.get('is_login', False)
    first_login = request.session.get('first_login', False)

    if request.method == 'POST':
        first_login = False
        orcid = request.session.get('orcid')
        name = request.POST.get('name')
        email = request.POST.get('email')
        Contact.objects.filter(orcid=orcid).update(name=name, email=email)
        request.session["name"] = name

    if is_login:
        info = Contact.objects.filter(
            orcid=request.session["orcid"]).values().first()
        return render(request, 'base/personal_info.html', {'info': info, 'first_login': first_login})
    else:
        messages.error(request, '請先登入')
        return render(request, 'base/personal_info.html')


def home(request):
    return render(request, 'base/home.html')


def get_species_data(request):
    now = timezone.now()
    last_updated = Species.objects.filter(status='I').aggregate(Min('last_updated'))['last_updated__min']
    has_new = Image.objects.filter(last_updated__gte=last_updated)
    if has_new.exists():
        Species.objects.filter(status='I').update(last_updated=now)
        for i in Species.DEFAULT_LIST:
            c = Image.objects.filter(species=i).count()
            if Species.objects.filter(status='I', name=i).exists():
                # if exist, update
                s = Species.objects.get(status='I', name=i)
                s.count = c
                s.last_updated = now
                s.save()
            else:  # else, create new
                if c > 0:
                    new_s = Species(
                        name=i,
                        count=c,
                        last_updated=now,
                        status='I'
                    )
                    new_s.save()
    # get data
    species_data = []
    with connection.cursor() as cursor:
        query = "SELECT count, name FROM taicat_species WHERE status = 'I' ORDER BY count DESC"
        cursor.execute(query)
        species_data = cursor.fetchall()
    response = {'species_data': species_data}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_geo_data(request):
    with connection.cursor() as cursor:
        query = """SELECT d.longitude, d.latitude, p.name, p.mode FROM taicat_deployment d 
                    JOIN taicat_project p ON p.id = d.project_id 
                    WHERE d.longitude IS NOT NULL and p.mode = 'official';"""
        cursor.execute(query)
        deployment_points = cursor.fetchall()
    response = {'deployment_points': deployment_points}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_growth_data(request):
    now = timezone.now()
    last_updated = HomePageStat.objects.all().aggregate(Min('last_updated'))['last_updated__min']
    has_new = Image.objects.filter(created__gte=last_updated)
    if has_new.exists():
        HomePageStat.objects.all().update(last_updated=now)
        # ------ update image --------- #
        data_growth_image = Image.objects.filter(created__gte=last_updated).annotate(year=ExtractYear('datetime')).values('year').annotate(num_image=Count('image_uuid', distinct=True)).order_by()
        data_growth_image = pd.DataFrame(data_growth_image, columns=['year', 'num_image']).sort_values('year')
        year_min, year_max = int(data_growth_image.year.min()), int(data_growth_image.year.max())
        year_gap = pd.DataFrame([i for i in range(year_min, year_max)], columns=['year'])
        data_growth_image = year_gap.merge(data_growth_image, how='left').fillna(0)
        data_growth_image['cumsum'] = data_growth_image.num_image.cumsum()
        data_growth_image = data_growth_image.drop(columns=['num_image'])
        for i in data_growth_image.index:
            row = data_growth_image.loc[i]
            if HomePageStat.objects.filter(year=row.year, type='image').exists():
                h = HomePageStat.objects.get(year=row.year, type='image')
                h.count += row['cumsum']
                h.save()
            else:
                new_h = HomePageStat(
                    type='image',
                    count=row['cumsum'],
                    last_updated=now,
                    year=row.year)
                new_h.save()
    data_growth_image = list(HomePageStat.objects.filter(type="image", year__gte=2008).order_by('year').values_list('year', 'count'))

    # --------- deployment --------- #
    year_gap = pd.DataFrame([i for i in range(2008, data_growth_image[-1][0]+1)], columns=['year'])
    with connection.cursor() as cursor:
        query = """
                WITH req As(
                    WITH base_request AS (
                            SELECT d.latitude, d.longitude, EXTRACT (year from taicat_project.start_date)::int AS start_year
                            FROM taicat_deployment d
                            JOIN taicat_project ON taicat_project.id = d.project_id 
                            WHERE d.longitude IS NOT NULL
                            GROUP BY start_year, d.latitude, d.longitude)
                            SELECT MIN(start_year) as year , latitude, longitude FROM base_request
                            GROUP BY latitude, longitude)
                    SELECT year, count(*) FROM req GROUP BY year
                """
        cursor.execute(query)
        data_growth_deployment = cursor.fetchall()
        data_growth_deployment = pd.DataFrame(data_growth_deployment, columns=['year', 'num_dep']).sort_values('year')
        data_growth_deployment = year_gap.merge(data_growth_deployment, how='left').fillna(0)
        data_growth_deployment['cumsum'] = data_growth_deployment.num_dep.cumsum()
        data_growth_deployment = data_growth_deployment.drop(columns=['num_dep'])
        data_growth_deployment = list(data_growth_deployment.itertuples(index=False, name=None))

    response = {'data_growth_image': data_growth_image,
                'data_growth_deployment': data_growth_deployment}

    return HttpResponse(json.dumps(response), content_type='application/json')


# ------ deprecated ------ #
# def stat_county(request):
#     city = request.GET.get('city')
#     with connection.cursor() as cursor:
#         query = """SELECT COUNT(DISTINCT(d.project_id)), COUNT (i.id)
#         FROM taicat_deployment d
#          JOIN taicat_image i ON i.deployment_id = d.id
#          where d.source_data->>'city' = '{}';"""

#         cursor.execute(query.format(city))
#         response = cursor.fetchone()
#     response = {"no_proj": response[0], "no_img": response[1]}
#     return HttpResponse(json.dumps(response), content_type='application/json')
