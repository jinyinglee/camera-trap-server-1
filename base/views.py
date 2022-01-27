from django.http import response
from django.shortcuts import render, HttpResponse, redirect
import json
from django.db import connection
from taicat.models import Deployment, HomePageStat, Image, Contact, Organization, Project, Species
from django.db.models import Count, Window, F, Sum, Min, Q, Max
from django.db.models.functions import ExtractYear
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.template import loader
import requests
from django.contrib import messages
from decimal import Decimal
import time
import pandas as pd
from django.utils import timezone
from datetime import datetime, timedelta


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def add_org_admin(request):
    if request.method == 'POST':
        print('hi')
        for i in request.POST:
            print(i)
        redirect(set_permission)


def login_for_test(request):
    next = request.GET.get('next')
    role = request.GET.get('role')
    print(next, role)
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

        return render(request, 'base/permission.html',
                      {'member_list': member_list, 'org_project_list': org_project_list, 'is_authorized': is_authorized,
                       'org_list': org_list, 'project_list': project_list, 'org_admin_list': org_admin_list})
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
        info = Contact.objects.filter(orcid=request.session["orcid"]).values().first()
        return render(request, 'base/personal_info.html', {'info': info, 'first_login': first_login})
    else:
        messages.error(request, '請先登入')
        return render(request, 'base/personal_info.html')


def home(request):
    return render(request, 'base/home.html')


def get_species_data(request):
    # TODO:
    # update if there is new image & species table not updated yet
    now = timezone.now()
    last_updated = Species.objects.filter(status='I').aggregate(Min('last_updated'))['last_updated__min']
    has_new = Image.objects.filter(created__gte=last_updated)
    if has_new.exists():
        for i in Species.DEFAULT_LIST:
            c = Image.objects.filter(created__gte=last_updated, annotation__contains=[{'species': i}]).count()
            if Species.objects.filter(status='I', name=i).exists():
                # if exist, update
                s = Species.objects.get(status='I', name=i)
                s.count += c
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
        query = """SELECT count, name from taicat_species where status = 'I'"""
        cursor.execute(query)
        species_data = cursor.fetchall()
    response = {'species_data': species_data}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_geo_data(request):
    with connection.cursor() as cursor:
        query = """SELECT d.longitude, d.latitude, p.name FROM taicat_deployment d 
                    JOIN taicat_project p ON p.id = d.project_id 
                    WHERE d.longitude IS NOT NULL;"""
        cursor.execute(query)
        deployment_points = cursor.fetchall()
    response = {'deployment_points': deployment_points}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_growth_data(request):

    # TODO:
    # update if there is new image & stat table not updated yet
    now = timezone.now()
    last_updated = timezone.now() - timedelta(days=10)  # pretend
    last_updated = HomePageStat.objects.all().aggregate(Min('last_updated'))['last_updated__min']

    has_new = Image.objects.filter(created__gte=last_updated)
    if has_new.exists():
        # ------ update image --------- #
        data_growth_image = Image.objects.filter(
            created__gte=last_updated).annotate(
            year=ExtractYear('datetime')).values('year').annotate(
            num_image=Count('id')).order_by()
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
                    year=row.year
                )
                new_h.save()
    data_growth_image = list(HomePageStat.objects.filter(type="image", year__gte=2008).values_list('year', 'count'))

    # --------- deployment --------- #
    year_gap = pd.DataFrame(
        [i for i in range(2008, data_growth_image[-1][0]+1)], columns=['year'])

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
