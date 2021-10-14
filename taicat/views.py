from django.db.models.fields import PositiveBigIntegerField
from django.http import response
from django.shortcuts import redirect, render, HttpResponse
from pandas.core.groupby.generic import DataFrameGroupBy
from .models import *
from django.db import connection  # for executing raw SQL
import re
import json
import math
from datetime import datetime, timedelta
from django.db.models import Count, Window, F, Sum, Min, Q
from django.contrib import messages
from django.core import serializers
import pandas as pd
from django.utils.http import urlquote
from decimal import Decimal
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from base.utils import generate_token
from django.conf import settings
import threading
import time
from ast import literal_eval

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

city_list = ['基隆市','嘉義市','台北市','嘉義縣','新北市','台南市',
            '桃園縣','高雄市','新竹市','屏東縣','新竹縣','台東縣',
            '苗栗縣','花蓮縣','台中市','宜蘭縣','彰化縣','澎湖縣',
            '南投縣','金門縣','雲林縣',	'連江縣']

species_list = ['水鹿','山羌','獼猴','山羊','野豬','鼬獾','白鼻心','食蟹獴','松鼠','飛鼠','黃喉貂','黃鼠狼','小黃鼠狼','麝香貓','黑熊','石虎','穿山甲','梅花鹿','野兔','蝙蝠']

q = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                EXTRACT (year from taicat_project.start_date)::int, \
                taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea, \
                COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                COUNT(DISTINCT(taicat_image.id)) AS num_image \
                FROM taicat_project \
                LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                LEFT JOIN taicat_deployment ON taicat_deployment.project_id = taicat_project.id \
                LEFT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                WHERE CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval \
                GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                ORDER BY taicat_project.start_date DESC;"


# [(319, 'bio', '', 2021, '', 0, 0, 0),(318, '開發', '', 2021, '', 0, 0, 0)]
# project_id, project name, project keywords, start year, num_studyarea, num_deployment, num_image


def sortFunction(value):
    return value["id"]


def check_if_authorized(request, pk):
    is_authorized = False
    member_id=request.session.get('id', None)
    if member_id:
        # check system_admin
        if Contact.objects.filter(id=member_id, is_system_admin=True):
            is_authorized = True
        # check project_member (project_admin)
        elif ProjectMember.objects.filter(member_id=member_id, role="project_admin", project_id=pk):
            is_authorized = True
        else:
            # check organization_admin
            if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
            if if_organization_admin:
                organization_id = if_organization_admin.values('organization').first()['organization']
                if Organization.objects.filter(id=organization_id,projects=pk):
                    is_authorized = True
    return is_authorized

def create_project(request):    
    if request.method == "POST":
        region_list = request.POST.getlist('region')
        region = {'region': ",".join(region_list)}

        data = dict(request.POST.items())
        data.pop('csrfmiddlewaretoken')
        data.update(region)

        project = Project.objects.create(**data)
        project_pk = project.id

        # save in taicat_project_member, default as project_admin
        ProjectMember.objects.create(role='project_admin',member_id=request.session['id'],project_id=project_pk)

        return redirect(edit_project_basic, project_pk)

    return render(request, 'project/create_project.html', {'city_list':city_list})


def edit_project_basic(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        if request.method == "POST":
            region_list = request.POST.getlist('region')
            region = {'region': ",".join(region_list)}

            data = dict(request.POST.items())
            data.pop('csrfmiddlewaretoken')
            data.update(region)

            project = Project.objects.filter(id=pk).update(**data)

        project = Project.objects.filter(id=pk).values().first()
        if project['region'] not in  ['', None, []]:
            region = {'region': project['region'].split(',')}
            project.update(region)

        return render(request, 'project/edit_project_basic.html', {'project': project, 'pk': pk,  'city_list': city_list, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk,'is_authorized': is_authorized})


def edit_project_license(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:

        if request.method == "POST":
            data = dict(request.POST.items())
            data.pop('csrfmiddlewaretoken')

            project = Project.objects.filter(id=pk).update(**data)

        project = Project.objects.filter(id=pk).values("publish_date","interpretive_data_license","identification_information_license","video_material_license").first()
        return render(request, 'project/edit_project_license.html', {'project': project, 'pk': pk, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk,'is_authorized': is_authorized})


def edit_project_members(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        # organization_admin
        # if project in organization
        organization_admin = [] # incase there is no one
        organization_id = Organization.objects.filter(projects=pk).values('id')
        for i in organization_id:
            temp = list(Contact.objects.filter(organization=i['id'], is_organization_admin=True).all().values('name','email'))
            organization_admin.extend(temp)
        
        # other members
        members = ProjectMember.objects.filter(project_id=pk).all()
        if request.method == "POST":
            data = dict(request.POST.items())
            # Add member
            if data['action'] == 'add':
                member = Contact.objects.filter(Q(email=data['contact_query'])|Q(orcid=data['contact_query'])).first()
                if member:            
                    # check: if not exists, create
                    if not ProjectMember.objects.filter(member_id=member.id, project_id=pk): 
                        ProjectMember.objects.create(role=data['role'], member_id=member.id, project_id=pk)
                    # check: if exists, update
                    else:
                        ProjectMember.objects.filter(member_id=member.id, project_id=pk).update(role=data['role'])
                    messages.success(request, '新增成功')
                else:
                    messages.error(request, '查無使用者')

            # Edit member
            elif data['action'] == 'edit':
                data.pop('action')
                data.pop('csrfmiddlewaretoken')
                for i in data:
                    ProjectMember.objects.filter(member_id=i, project_id=pk).update(role=data[i])
                messages.success(request, '儲存成功')
            # Remove member
            else:
                ProjectMember.objects.filter(member_id=data['memberid'], project_id=pk).delete()
                messages.success(request, '移除成功')

        return render(request, 'project/edit_project_members.html', {'members': members, 'pk': pk, 
                                                                    'organization_admin':organization_admin,
                                                                    'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk,'is_authorized': is_authorized})


def edit_project_deployment(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        project = Project.objects.filter(id=pk)
        study_area = StudyArea.objects.filter(project_id=pk)

        return render(request, 'project/edit_project_deployment.html', {'project': project, 'pk': pk, 
                    'study_area': study_area, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk,'is_authorized': is_authorized})


def get_deployment(request):
    if request.method == "POST":
        id = request.POST.get('study_area_id')

        with connection.cursor() as cursor:
            query =  """SELECT id, name, longitude, latitude, altitude, landcover, vegetation, verbatim_locality FROM taicat_deployment WHERE study_area_id = {};
                        """
            cursor.execute(query.format(id))
            data = cursor.fetchall()

        return HttpResponse(json.dumps(data, cls=DecimalEncoder), content_type='application/json')


def add_deployment(request):
    if request.method == "POST":
        res = request.POST

        project_id = res.get('project_id')
        study_area_id = res.get('study_area_id')
        geodetic_datum = res.get('geodetic_datum')
        
        names = res.getlist('names[]')
        longitudes = res.getlist('longitudes[]')
        latitudes = res.getlist('latitudes[]')
        altitudes = res.getlist('altitudes[]')
        landcovers = res.getlist('landcovers[]')
        vegetations = res.getlist('vegetations[]')

        for i in range(len(names)):
            if altitudes[i] == "":
                altitudes[i] = None
            Deployment.objects.create(project_id=project_id, study_area_id=study_area_id, geodetic_datum=geodetic_datum,
                                    name=names[i], longitude=longitudes[i], latitude=latitudes[i], altitude=altitudes[i],landcover=landcovers[i],
                                    vegetation=vegetations[i])

        return HttpResponse(json.dumps({'d': 'done'}), content_type='application/json')



def add_studyarea(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        parent_id = request.POST.get('parent_id', None)
        name = request.POST.get('name')

        s = StudyArea.objects.create(name=name, project_id=project_id, parent_id=parent_id)
        data = {'study_area_id': s.id }

        return HttpResponse(json.dumps(data), content_type='application/json')


def project_overview(request):
    public_project = []
    my_project = []
    my_species_data = []
    # TODO
    # 公開計畫 depend on publish_date date
    with connection.cursor() as cursor:
        q = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                        EXTRACT (year from taicat_project.start_date)::int, \
                        taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea \
                        FROM taicat_project \
                        LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                        WHERE CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval \
                        GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                        ORDER BY taicat_project.start_date DESC;"
        cursor.execute(q)
        public_project_info = cursor.fetchall()
        public_project_info = pd.DataFrame(public_project_info, columns=['id','name','keyword', 'start_year', 'funding_agency', 'num_studyarea'])

    with connection.cursor() as cursor:
        q = "SELECT \
                        taicat_deployment.project_id, COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                        COUNT(DISTINCT(taicat_image.id)) AS num_image \
                        FROM taicat_deployment \
                        LEFT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                        GROUP BY taicat_deployment.project_id \
                        ORDER BY taicat_deployment.project_id DESC;"
        cursor.execute(q)   
        public_img_info = cursor.fetchall()
        public_img_info = pd.DataFrame(public_img_info, columns=['id','num_deployment','num_image'])

    public_project = pd.merge(public_project_info,public_img_info,how='left')
    public_project[['num_deployment', 'num_image', 'num_studyarea']] = public_project[['num_deployment', 'num_image', 'num_studyarea']].fillna(0)
    public_project = public_project.astype({'num_deployment': 'int', 'num_image': 'int', 'num_studyarea': 'int'})
    public_project = list(public_project.itertuples(index=False, name=None))
    # my project    
    project_list = []
    member_id=request.session.get('id', None)
    if member_id:
        # 1. select from project_member table
        with connection.cursor() as cursor:
            query = "SELECT project_id FROM taicat_projectmember where member_id ={}"
            cursor.execute(query.format(member_id))
            temp = cursor.fetchall()
            for i in temp:
                project_list += [i[0]]
        # 2. check if the user is organization admin
        if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
        if if_organization_admin:
            organization_id = if_organization_admin.values('organization').first()['organization']
            temp = Organization.objects.filter(id=organization_id).values('projects')
            for i in temp:
                project_list += [i['projects']]
        if project_list:
            project_list = str(project_list).replace('[', '(').replace(']',')')
            with connection.cursor() as cursor:
                q = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                                EXTRACT (year from taicat_project.start_date)::int, \
                                taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea \
                                FROM taicat_project \
                                LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                                WHERE taicat_project.id IN {} \
                                GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                                ORDER BY taicat_project.start_date DESC;"
                cursor.execute(q.format(project_list))
                my_project_info = cursor.fetchall()
                my_project_info = pd.DataFrame(my_project_info, columns=['id','name','keyword', 'start_year', 'funding_agency', 'num_studyarea'])

            with connection.cursor() as cursor:
                q = "SELECT \
                                taicat_deployment.project_id, COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                                COUNT(DISTINCT(taicat_image.id)) AS num_image \
                                FROM taicat_deployment \
                                LEFT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                                WHERE taicat_deployment.project_id IN {} \
                                GROUP BY taicat_deployment.project_id \
                                ORDER BY taicat_deployment.project_id DESC;"
                cursor.execute(q.format(project_list))
                my_img_info = cursor.fetchall()
                my_img_info = pd.DataFrame(my_img_info, columns=['id','num_deployment','num_image'])

            my_project = pd.merge(my_project_info,my_img_info,how='left')
            my_project[['num_deployment', 'num_image', 'num_studyarea']] = my_project[['num_deployment', 'num_image', 'num_studyarea']].fillna(0)
            my_project = my_project.astype({'num_deployment': 'int', 'num_image': 'int', 'num_studyarea': 'int'})
            my_project = list(my_project.itertuples(index=False, name=None))

            with connection.cursor() as cursor:
                query =  """with base_request as ( 
                            SELECT 
                                x.*, 
                                i.id FROM taicat_image i
                                CROSS JOIN LATERAL
                                json_to_recordset(i.annotation::json) x 
                                        ( species text) 
                                WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                                    SELECT d.id FROM taicat_deployment d
                                    WHERE d.project_id IN {}
                                ) )
                        select count(id), species from base_request
                        group by species;
                        """
                cursor.execute(query.format(project_list))
                my_species_data = cursor.fetchall()

    with connection.cursor() as cursor:
        query =  """with base_request as ( 
                    SELECT 
                        x.*, 
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text) 
                        WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                            SELECT d.id FROM taicat_deployment d
                            JOIN taicat_project p ON p.id = d.project_id
                            WHERE CURRENT_DATE >= p.publish_date OR p.end_date < now() - '5 years' :: interval 
                        ) )
                select count(id), species from base_request
                group by species;
                """
        cursor.execute(query)
        public_species_data = cursor.fetchall()
    public_species_data = [ x for x in public_species_data if x[1] in species_list ]
    public_species_data.sort()
    my_species_data = [ x for x in my_species_data if x[1] in species_list ]
    my_species_data.sort()

    return render(request, 'project/project_overview.html', {'public_project': public_project, 'my_project': my_project, 
                                                            'public_species_data':public_species_data, 'my_species_data':my_species_data})

def update_datatable(request):
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        species = request.POST.getlist('species[]')
        if species != ['']:
            species = str(species).replace('[', '(').replace(']',')')
            species = f"where species in {species}"
        else:
            species = ''
        project_list = []           
        if table_id == 'publicproject':
            with connection.cursor() as cursor:
                query =  """with base_request as ( 
                            SELECT 
                                x.*, 
                                i.id, i.deployment_id FROM taicat_image i
                                CROSS JOIN LATERAL
                                json_to_recordset(i.annotation::json) x 
                                        ( species text) 
                                WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                                    SELECT d.id FROM taicat_deployment d
                                    JOIN taicat_project p ON p.id = d.project_id
                                    WHERE CURRENT_DATE >= p.publish_date OR p.end_date < now() - '5 years' :: interval 
                                ) )
                        select distinct(project_id) from taicat_deployment where id in (select distinct(deployment_id) from base_request {});
                        """
                cursor.execute(query.format(species))
                temp = cursor.fetchall()
                for i in temp:
                    project_list += [i[0]]

        else:
            my_project_list = []
            member_id=request.session.get('id', None)
            if member_id:
                # 1. select from project_member table
                with connection.cursor() as cursor:
                    query = "SELECT project_id FROM taicat_projectmember where member_id ={}"
                    cursor.execute(query.format(member_id))
                    temp = cursor.fetchall()
                    for i in temp:
                        my_project_list += [i[0]]
                # 2. check if the user is organization admin
                if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
                if if_organization_admin:
                    organization_id = if_organization_admin.values('organization').first()['organization']
                    temp = Organization.objects.filter(id=organization_id).values('projects')
                    for i in temp:
                        my_project_list += [i['projects']]
                
                # check species
                if my_project_list:
                    with connection.cursor() as cursor:
                        species = str(species).replace('[', '(').replace(']',')')
                        my_project_list = str(my_project_list).replace('[', '(').replace(']',')')
                        query =  """with base_request as ( 
                                    SELECT 
                                        x.*, 
                                        i.id, i.deployment_id FROM taicat_image i
                                        CROSS JOIN LATERAL
                                        json_to_recordset(i.annotation::json) x 
                                                ( species text) 
                                        WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                                            SELECT d.id FROM taicat_deployment d
                                            WHERE d.project_id IN {} 
                                        ) )
                                select distinct(project_id) from taicat_deployment where id in (select distinct(deployment_id) from base_request {});
                                """
                        cursor.execute(query.format(my_project_list,species))
                        temp = cursor.fetchall()
                        for i in temp:
                            project_list += [i[0]]
        
        if project_list:
            project_list = str(project_list).replace('[', '(').replace(']',')')
            project = []
            with connection.cursor() as cursor:
                query = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                                EXTRACT (year from taicat_project.start_date)::int, \
                                taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea, \
                                COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                                COUNT(DISTINCT(taicat_image.id)) AS num_image \
                                FROM taicat_project \
                                LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                                LEFT JOIN taicat_deployment ON taicat_deployment.project_id = taicat_project.id \
                                LEFT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                                WHERE taicat_project.id IN {}\
                                GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                                ORDER BY taicat_project.created DESC;"
                cursor.execute(query.format(project_list))
                project = cursor.fetchall()
                
    return HttpResponse(json.dumps(project), content_type='application/json')


def data(request):
    s = time.time()
    requests = request.POST
    pk = requests.get('pk')
    start_date = requests.get('start_date')
    end_date = requests.get('end_date')
    date_filter = ''
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        date_filter = "AND i.datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)
    _start = requests.get('start')
    _length = requests.get('length')
    species = requests.get('species')
    conditions = ''
    deployment = requests.getlist('deployment[]')
    sa = requests.get('sa')
    if sa:
        conditions += f' AND sa.id = {sa}'
        if deployment:
            if 'all' not in deployment:
                x = [int(i) for i in deployment]
                x = str(x).replace('[','(').replace(']',')')
                conditions += f' AND d.id IN {x}'
        else:
            conditions = 'AND d.id IS NULL'
    spe_conditions = ''
    if species:
        spe_conditions = "AND annotation::text like '%黃鼠狼%' "

    with connection.cursor() as cursor:
        query = """SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, 
                        to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        sa.parent_id AS saparent, i.annotation, i.file_url, i.id, i.from_mongo 
                        FROM taicat_image i
                        JOIN taicat_deployment d ON d.id = i.deployment_id
                        JOIN taicat_studyarea sa ON sa.id = d.study_area_id 
                        WHERE d.project_id = {} {} {} {}
                        ORDER BY i.created, i.filename;"""
        cursor.execute(query.format(pk, date_filter, conditions, spe_conditions))
        image_info = cursor.fetchall()

    if image_info:
        df = pd.DataFrame(image_info, columns=['saname','dname','filename','datetime','saparent','annotation','file_url','image_id','from_mongo'])
        # parse string to list
        df['anno_list'] = df.annotation.apply(lambda x: literal_eval(str(x)))
        # separate dictionary to columns
        df = df.explode('anno_list')
        df = pd.concat([df.drop(['anno_list'], axis=1), df['anno_list'].apply(pd.Series)], axis=1)
        df = df.reset_index()            
        
        start = int(_start)
        length = int(_length)
        page = math.ceil(start / length) + 1
        per_page = length
        recordsTotal = len(df)
        recordsFiltered = len(df)
        
        # 只保留該頁顯示的比數
        df = df[start:start + length]

        # add group id
        df['group_id'] = df.groupby('index').cumcount()
        ssa_exist = StudyArea.objects.filter(project_id=pk, parent__isnull=False)
        if ssa_exist.count() > 0:
            ssa_list = list(ssa_exist.values_list('name', flat=True))
            for i in df[df.saname.isin(ssa_list)].index:
                try: 
                    parent_saname = StudyArea.objects.get(id=df.saparent[i]).name
                    current_name = df.saname[i]
                    df.loc[i,'saname'] = f"{current_name}_{parent_saname}"
                except:
                    pass

        df = df.where(pd.notnull(df), None)

        for i in df.index:
            file_url = df.file_url[i]
            if not file_url:
                file_url = f"{df.image_id[i]}-m.jpg"
            extension = file_url.split('.')[-1]
            if not df.from_mongo[i]: 
                # new data - image
                if extension == 'jpg':
                    df.loc[i,'file_url'] =  """<img class="img lazy mx-auto d-block" style="height: 100px" data-src="https://camera-trap-21.s3-ap-northeast-1.amazonaws.com/{}" />""".format(file_url)
                # new data - video
                else:
                    df.loc[i, 'file_url'] =  """
                    <video class="img lazy mx-auto d-block" controls height="100">
                        <source src="https://camera-trap-21.s3-ap-northeast-1.amazonaws.com/{}"
                                type="video/webm">
                        <source src="https://camera-trap-21.s3-ap-northeast-1.amazonaws.com/{}"
                                type="video/mp4">
                        抱歉，您的瀏覽器不支援內嵌影片。
                    </video>
                    """.format(file_url,file_url)
            else:
                # old data - image
                if extension == 'jpg':
                    df.loc[i,'file_url'] =  """<img class="img lazy mx-auto d-block" style="height: 100px" data-src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{}" />""".format(file_url)
                # old data - video
                else:
                    df.loc[i,'file_url'] =  """
                    <video class="img lazy mx-auto d-block" controls height="100">
                        <source src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-videos/{}"
                                type="video/webm">
                        <source src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-videos/{}"
                                type="video/mp4">
                        抱歉，您的瀏覽器不支援內嵌影片。
                    </video>
                    """.format(file_url,file_url)
            ### videos: https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/video ##

        data = df[['saname','dname','filename','datetime','species','lifestage','sex','antler','animal_id','remarks','file_url','group_id','image_id']]
        data = data.to_dict('records')

        response = {
            'data': data,
            'page': page, 
            'per_page': per_page, 
            'recordsTotal': recordsTotal,
            'recordsFiltered': recordsFiltered,
        }
    
    else:
        response = {
            'data': [],
            'page': 0, 
            'per_page': 0,
            'recordsTotal': 0,
            'recordsFiltered': 0,
        }

    return HttpResponse(json.dumps(response), content_type='application/json')
    

def project_detail(request, pk):
    is_authorized = check_if_authorized(request, pk)
    with connection.cursor() as cursor:
        query = "SELECT name, funding_agency, code, " \
                "principal_investigator, " \
                "to_char(start_date, 'YYYY-MM-DD'), " \
                "to_char(end_date, 'YYYY-MM-DD') FROM taicat_project WHERE id={}"
        cursor.execute(query.format(pk))
        project_info = cursor.fetchone()
    project_info = list(project_info)
    # deployment = Deployment.objects.filter(project_id=pk).values('name','id').exclude(name=[None, '']).distinct().order_by('name') 
    deployment = Deployment.objects.filter(project_id=pk)
    with connection.cursor() as cursor:
        query =  """with base_request as ( 
                    SELECT 
                        x.*, 
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text) 
                        WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                            SELECT d.id FROM taicat_deployment d
                            WHERE d.project_id = {}
                        ) )
                select count(id), species from base_request
                group by species;
                """
        cursor.execute(query.format(pk))
        species = cursor.fetchall()
        species = [x for x in species if x[1] is not None and x[1] != '' ] 
        species = [ (x[0], x[1].replace('\\','')) for x in species]
        species.sort(key = lambda x: x[1])
    image_objects = Image.objects.filter(deployment__project__id=pk)
    if image_objects.count() > 0:
        latest_date = image_objects.latest('datetime').datetime.strftime("%Y-%m-%d")
        earliest_date = image_objects.earliest('datetime').datetime.strftime("%Y-%m-%d")
    else:
        latest_date, earliest_date = None, None
    # edit permission
    user_id = request.session.get('id', None)
    edit = False
    if user_id:
        # 系統管理員 / 個別計畫承辦人
        if Contact.objects.filter(id=user_id, is_system_admin=True).first() or ProjectMember.objects.filter(member_id=user_id, role="project_admin", project_id=pk):
            edit = True
        # 計畫總管理人
        elif Contact.objects.filter(id=user_id, is_organization_admin=True):
            organization_id = Contact.objects.filter(id=user_id, is_organization_admin=True).values('organization').first()['organization']
            if Organization.objects.filter(id=organization_id,projects=pk):
                edit = True
    study_area = StudyArea.objects.filter(project_id=pk).order_by('name')
    return render(request, 'project/project_detail.html',
                {'project_name': len(project_info[0]),'project_info': project_info, 'species': species, 'pk': pk,
                'study_area':study_area, 'deployment':deployment,
                'earliest_date': earliest_date, 'latest_date':latest_date,
                'edit': edit, 'is_authorized': is_authorized})


def edit_image(request, pk):
    # get original annotation first
    requests = request.POST
    image_id = requests.get('id')
    anno = Image.objects.get(id=image_id).annotation
    group_id = int(requests.get('group_id'))
    species = requests.get('species')
    lifestage = requests.get('lifestage')
    sex = requests.get('sex')
    antler = requests.get('antler')
    animal_id = requests.get('animal_id')
    remarks = requests.get('remarks')
    anno[group_id] = {'species': species, 'lifestage': lifestage, 'sex': sex, 'antler': antler,
                            'animal_id': animal_id, 'remarks': remarks}
    # write back to db
    obj = Image.objects.get(id=image_id)
    obj.annotation = anno
    obj.save()

    # update filter species options
    with connection.cursor() as cursor:
        query =  """with base_request as ( 
                    SELECT 
                        x.*, 
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text) 
                        WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                            SELECT d.id FROM taicat_deployment d
                            WHERE d.project_id = {}
                        ) )
                select count(id), species from base_request
                group by species;
                """
        cursor.execute(query.format(pk))
        species = cursor.fetchall()
        species = [x for x in species if x[1] is not None and x[1] != '' ] 
        species.sort(key = lambda x: x[1])


    response = {'species': species}
    return HttpResponse(json.dumps(response), content_type='application/json')


def download_request(request, pk):
    requests = request.POST
    start_date = requests.get('start_date')
    end_date = requests.get('end_date')
    data_filter = ''
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        data_filter = "AND i.datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)
    species = requests.get('species-filter')
    conditions = ''
    deployment = requests.getlist('deployment[]')
    sa = requests.get('sa')
    if sa:
        conditions += f' AND sa.id = {sa}'
        if deployment:
            if 'all' not in deployment:
                x = [int(i) for i in deployment]
                x = str(x).replace('[','(').replace(']',')')
                conditions += f' AND d.id IN {x}'
        else:
            conditions = 'AND d.id IS NULL'

    with connection.cursor() as cursor:
        query = """with base_request as ( 
                    SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, 
                        to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        x.*, i.file_url, 
                        sa.parent_id AS saparent,
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text, lifestage text , sex text, 
                                    antler text, remarks text, animal_id text ) 
                        JOIN taicat_deployment d ON d.id = i.deployment_id
                        JOIN taicat_studyarea sa ON sa.id = d.study_area_id 
                        WHERE d.project_id= {} {} {}
                        ORDER BY i.created, i.filename)
                select row_to_json(t) from ( 
                    select 1 as draw, 
                    ( select array_to_json(array_agg(row_to_json(u)))
                        from (select * from base_request) u
                    ) as data) t;"""
        cursor.execute(query.format(pk, data_filter, conditions))
        image_info = cursor.fetchall()
        data = image_info[0][0]['data']

    if data:
        data = sorted(data, key=sortFunction)
        if species != "":
            data = [i for i in data if i['species'] == species]
        # add sub-studyarea if exists
        for i in range(len(data)):
            data[i].update({'subsaname': None})
            if StudyArea.objects.filter(id=data[i]['saparent']):
                parent_saname = StudyArea.objects.get(id=data[i]['saparent']).name
                saname = data[i]['saname']
                data[i].update({'saname': parent_saname})
                data[i].update({'subsaname': saname})
        df = pd.DataFrame(data)
        df['計畫名稱'] = Project.objects.get(id=pk).name
        df['計畫ID'] = pk
        # rename
        df = df.rename(columns={'saname':'樣區', 'dname':'相機位置', 'filename':'檔名', 'datetime':'拍攝時間', 'species':'物種',
            'lifestage':'年齡', 'sex':'性別', 'antler':'角況', 'remarks':'備註', 'animal_id':'個體ID', 'id':'影像ID',
            'subsaname':'子樣區'})
        # subset and change column order
        cols = ['計畫ID','計畫名稱','影像ID','樣區','子樣區','相機位置','檔名','拍攝時間','物種','年齡','性別','角況','個體ID','備註']
        df = df[cols]
        # df = df[df.columns.intersection(cols)]
    else:
        df = pd.DataFrame() # no data

    n = f'download_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] =  'attachment; filename={}'.format(urlquote(n))                                  
    df.to_excel(response, index=False)

    return response
    

# send download link

class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_verification_email(user, request):
    current_site = get_current_site(request)  # the domain user is on

    email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
    email_body = render_to_string('account/verification.html',{
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,
    to=[user.username])

    EmailThread(email).start()



def download_data(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True
        user.save()

        messages.add_message(request, messages.SUCCESS,
                            '驗證成功！請立即設定您的密碼')
        login(request, user, backend='account.views.registerBackend') 
        return redirect(reverse('personal_info'))

    return render(request, 'account/verification-fail.html', {"user": user})
