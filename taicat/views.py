from django.http import response
from django.shortcuts import redirect, render, HttpResponse
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

from decimal import Decimal

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
    # 公開計畫 depend on publish_date date
    with connection.cursor() as cursor:
        cursor.execute("SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
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
                        ORDER BY taicat_project.created DESC;")
        public_project = cursor.fetchall()

    # my project    
    project_list = []
    member_id=request.session.get('id', None)
    print('member_id', member_id)
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
            with connection.cursor() as cursor:
                project_list = str(project_list).replace('[', '(').replace(']',')')
                query = 'SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                                EXTRACT (year from taicat_project.start_date)::int, \
                                taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea, \
                                COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                                COUNT(DISTINCT(taicat_image.id)) AS num_image \
                                FROM taicat_project \
                                LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                                LEFT JOIN taicat_deployment ON taicat_deployment.project_id = taicat_project.id \
                                LEFT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                                WHERE taicat_project.id IN {} \
                                GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                                ORDER BY taicat_project.created DESC;'
                cursor.execute(query.format(project_list))
                my_project = cursor.fetchall()

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


    # "RIGHT JOIN" when upload to server

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
    my_species_data = [ x for x in my_species_data if x[1] in species_list ]

    return render(request, 'project/project_overview.html', {'public_project': public_project, 'my_project': my_project, 
                                                            'public_species_data':public_species_data, 'my_species_data':my_species_data})

def update_datatable(request):
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        species = request.POST.getlist('species[]')
        project_list = []           
        if table_id == 'publicproject':
            with connection.cursor() as cursor:
                species = str(species).replace('[', '(').replace(']',')')
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
                        select distinct(project_id) from taicat_deployment where id in (select distinct(deployment_id) from base_request where species in {});
                        """
                cursor.execute(query.format(species))
                temp = cursor.fetchall()
                for i in temp:
                    print(i[0])
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
                                select distinct(project_id) from taicat_deployment where id in (select distinct(deployment_id) from base_request where species in {});
                                """
                        cursor.execute(query.format(my_project_list,species))
                        temp = cursor.fetchall()
                        for i in temp:
                            print(i[0])
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
    requests = request.POST
    pk = requests.get('pk')
    start_date = requests.get('start_date')
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = requests.get('end_date')
    end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    _start = requests.get('start')
    _length = requests.get('length')
    species = requests.get('species')
    deployment = requests.get('deployment')
    sa = requests.get('sa')

    with connection.cursor() as cursor:
        query = """with base_request as ( 
                    SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, 
                        to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        x.*, i.file_url, 
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text, lifestage text , sex text, 
                                  antler text, remarks text, animal_id text ) 
                        JOIN taicat_deployment d ON d.id = i.deployment_id
                        JOIN taicat_studyarea sa ON sa.id = d.study_area_id 
                        WHERE d.project_id= {} AND i.datetime BETWEEN '{}' AND '{}' 
                        ORDER BY i.created, i.filename)
                select row_to_json(t) from ( 
                    select 1 as draw, 
                    ( select array_to_json(array_agg(row_to_json(u)))
                        from (select * from base_request) u
                    ) as data) t;"""
        cursor.execute(query.format(pk, start_date, end_date))
        image_info = cursor.fetchall()
        data = image_info[0][0]['data']

    if data:
        if species != "":
            data = [i for i in data if i['species'] == species]
        if sa != "":
            data = [i for i in data if i['saname'] == sa]
        if deployment != "":
            data = [i for i in data if i['dname'] == deployment]

        def sortFunction(value):
            return value["id"]
        data = sorted(data, key=sortFunction)

        recordsTotal = len(data)
        recordsFiltered = len(data)

        for i in range(len(data)):
            if data[i]['species']:
                data[i]['species'] = re.sub(r'^"|"$', '', data[i]['species'])
            else:
                data[i]['species'] = ''
            if data[i]['lifestage']:
                data[i]['lifestage'] = re.sub(r'^"|"$', '', data[i]['lifestage'])
            else:
                data[i]['lifestage'] = ''
            file_url = data[i].get('file_url', '')
            if not file_url:
                file_url = f"{data[i]['id']}-m.jpg"
            data[i]['file_url'] =  """<img class="img lazy" style="height: 200px" data-src="https://camera-trap-21.s3-ap-northeast-1.amazonaws.com/{}" />""".format(file_url)

        # add group_id if more than one annotation in a image
        if data:
            df = pd.DataFrame(data)
            group_id = df.groupby('id').cumcount()
            for i in range(len(data)):
                data[i].update({'group_id': str(group_id[i])})

        if _start and _length:
            start = int(_start)
            length = int(_length)
            page = math.ceil(start / length) + 1
            per_page = length
            data = data[start:start + length]

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
    with connection.cursor() as cursor:
        query = "SELECT name, funding_agency, code, " \
                "principal_investigator, " \
                "to_char(start_date, 'YYYY-MM-DD'), " \
                "to_char(end_date, 'YYYY-MM-DD') FROM taicat_project WHERE id={}"
        cursor.execute(query.format(pk))
        project_info = cursor.fetchone()
    project_info = list(project_info)

    studyarea = StudyArea.objects.filter(project_id=pk).values('name').exclude(name=[None, '']).distinct().order_by('name') 
    deployment = Deployment.objects.filter(project_id=pk).values('name','id').exclude(name=[None, '']).distinct().order_by('name') 

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
        species = [ x[1] for x in species]

    latest_date = Image.objects.latest('datetime').datetime.strftime("%Y-%m-%d")
    earliest_date = Image.objects.earliest('datetime').datetime.strftime("%Y-%m-%d")

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

    return render(request, 'project/project_detail.html',
                {'project_info': project_info, 'species': species, 'pk': pk,
                'studyarea':studyarea, 'deployment':deployment,
                'earliest_date': earliest_date, 'latest_date':latest_date,
                'edit': edit})


def edit_image(request, pk):
    print(request.POST)
    print(pk)
    response = {}
    return HttpResponse(json.dumps(response), content_type='application/json')


with connection.cursor() as cursor:
    query = "SELECT annotation FROM taicat_image where id=594"
    cursor.execute(query)
    temp = cursor.fetchone()[0]

# 沒有 1858 '[]'
# 一個 438 '[{"sex": "", "antler": "", "remarks": "", "species": "", "animal_id": "", "lifestage": ""}]' 
# 多個 594  '[{"sex": "", "antler": "", "remark": "", "species": "測試", "animal_id": "", "lifestage": ""}, {"sex": "", "antler": "", "remark": "", "species": "測試", "animal_id": "", "lifestage": ""}]'
# https://stackoverflow.com/questions/18209625/how-do-i-modify-fields-inside-the-new-postgresql-json-datatype