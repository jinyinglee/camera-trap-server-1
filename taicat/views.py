from django.db.models.fields import PositiveBigIntegerField
from django.http import response, JsonResponse
from django.shortcuts import redirect, render, HttpResponse
from pandas.core.groupby.generic import DataFrameGroupBy
from taicat.models import *
from django.db import connection  # for executing raw SQL
import re
import json
import math
import datetime
# from datetime import datetime, timedelta, timezone
from django.db.models import Count, Window, F, Sum, Min, Q, Max, Func, Value, CharField
from django.db.models.functions import Trunc, ExtractYear
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
import numpy as np
from conf.settings import env
import os
from django.core.mail import send_mail
import threading
import string
import random
from calendar import monthrange, monthcalendar
from .utils import (
    Calculation,
    find_deployment_working_day,
)
import collections
from operator import itemgetter
from dateutil import parser
from django.test.utils import CaptureQueriesContext

s3_bucket = env('S3_BUCKET', default='camera-trap-21-prod')


def delete_data(request, pk):
    if request.method == "POST":
        now = timezone.now()
        image_list = request.POST.getlist('image_id[]')
        print(image_list)
        image_objects = Image.objects.filter(id__in=image_list)
        # species的資料先用id抓回來計算再扣掉
        query = image_objects.values('species').annotate(total=Count('species')).order_by('-total')
        for q in query:
            print(q['species'], q['total'])
            # taicat_species
            if sp := Species.objects.filter(name=q['species']).first():
                if sp.count == q['total']:
                    sp.delete()
                else:
                    sp.count -= q['total']
                    sp.last_updated = now
                    sp.save()
            # taicat_projectspecies
            if p_sp := ProjectSpecies.objects.filter(name=q['species'], project_id=pk).first():
                if p_sp.count == q['total']:
                    p_sp.delete()
                else:
                    p_sp.count -= q['total']
                    p_sp.last_updated = now
                    p_sp.save()

        if ProjectStat.objects.filter(project_id=pk).exists():
            p = ProjectStat.objects.get(project_id=pk)
            p.num_data -= image_objects.count()
            p.last_updated = now
            p.save()

        year = image_objects.aggregate(Min('datetime'))['datetime__min'].strftime("%Y")
        home = HomePageStat.objects.filter(year__gte=year)
        for h in home:
            h.count -= image_objects.count()
            h.last_updated = now
            h.save()

        # move deleted image to DeletedImage table
        image_dict = image_objects.values()
        for d in image_dict:
            di = DeletedImage(**d)
            di.save()
        Image.objects.filter(id__in=image_list).delete()

    species = ProjectSpecies.objects.filter(project_id=pk).order_by('count').values('count', 'name')
    response = {'species': list(species)}
    return JsonResponse(response, safe=False)  # or JsonResponse({'data': data})


def edit_image(request, pk):
    if request.method == "POST":
        now = timezone.now()
        requests = request.POST
        image_id = requests.get('image_id')
        image_id = image_id.split(',')

        keys = ['species', 'life_stage', 'sex', 'antler', 'animal_id', 'remarks']
        updated_dict = {}
        for k in keys:
            updated_dict.update({k: requests.get(k)})

        if requests.get('studyarea_id'):
            updated_dict.update({'studyarea_id': requests.get('studyarea_id')})
        if requests.get('deployment_id'):
            updated_dict.update({'deployment_id': requests.get('deployment_id')})

        # TODO: update species stat
        obj = Image.objects.filter(id__in=image_id)
        c = obj.count()  # 更新的照片數量

        # 抓原本的回來減掉
        species = requests.get('species')
        query = obj.values('species').annotate(total=Count('species')).order_by('-total')
        for q in query:
            # taicat_species
            if sp := Species.objects.filter(name=q['species']).first():
                if sp.count == q['total']:
                    sp.delete()
                else:
                    sp.count -= q['total']
                    sp.last_updated = now
                    sp.save()
            # taicat_projectspecies
            if p_sp := ProjectSpecies.objects.filter(name=q['species'], project_id=pk).first():
                if p_sp.count == q['total']:
                    p_sp.delete()
                else:
                    p_sp.count -= q['total']
                    p_sp.last_updated = now
                    p_sp.save()
        # 新的加上去
        if sp := Species.objects.filter(name=species).first():
            sp.count += c
            sp.last_updated = now
            sp.save()
        else:
            sp = Species(name=species, last_updated=now, count=c)
            if species in Species.DEFAULT_LIST:
                sp.status = 'I'
            sp.save()

        # taicat_projectspecies
        if p_sp := ProjectSpecies.objects.filter(name=species, project_id=pk).first():
            p_sp.count += c
            p_sp.last_updated = now
            p_sp.save()
        else:
            p_sp = ProjectSpecies(
                name=species,
                last_updated=now,
                count=c,
                project_id=pk)
            p_sp.save()

        if updated_dict:
            updated_dict.update({'last_updated': now})
            obj.update(**updated_dict)

    species = ProjectSpecies.objects.filter(project_id=pk).order_by('count').values('count', 'name')
    response = {'species': list(species)}
    return JsonResponse(response, safe=False)  # or JsonResponse({'data': data})


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


city_list = ['基隆市', '嘉義市', '台北市', '嘉義縣', '新北市', '台南市',
             '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '台東縣',
             '苗栗縣', '花蓮縣', '台中市', '宜蘭縣', '彰化縣', '澎湖縣',
             '南投縣', '金門縣', '雲林縣',	'連江縣']

species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']


def sortFunction(value):
    return value["id"]


def check_if_authorized(request, pk):
    is_authorized = False
    member_id = request.session.get('id', None)
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
                if Organization.objects.filter(id=organization_id, projects=pk):
                    is_authorized = True
    return is_authorized


def check_if_authorized_create(request):
    is_authorized = False
    member_id = request.session.get('id', None)
    if member_id:
        if Contact.objects.filter(id=member_id, is_system_admin=True):
            is_authorized = True
        # 如果是任何計畫的承辦人
        elif ProjectMember.objects.filter(member_id=member_id, role="project_admin"):
            is_authorized = True
        elif Contact.objects.filter(id=member_id, is_organization_admin=True):
            is_authorized = True
    return is_authorized


def create_project(request):
    is_authorized_create = check_if_authorized_create(request)

    if request.method == "POST":
        region_list = request.POST.getlist('region')
        region = {'region': ",".join(region_list)}

        data = dict(request.POST.items())
        data.pop('csrfmiddlewaretoken')
        data.update(region)

        project = Project.objects.create(**data)
        project_pk = project.id

        # save in taicat_project_member, default as project_admin
        ProjectMember.objects.create(role='project_admin', member_id=request.session['id'], project_id=project_pk)

        return redirect(edit_project_basic, project_pk)

    return render(request, 'project/create_project.html', {'city_list': city_list, 'is_authorized_create': is_authorized_create})


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
        # replace None in dictionary
        for k, v in project.items():
            if v is None or v == 'None':
                project[k] = ""

        if project['region'] not in ['', None, []]:
            region = {'region': project['region'].split(',')}
            project.update(region)
        return render(request, 'project/edit_project_basic.html', {'project': project, 'pk': pk,  'city_list': city_list, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk, 'is_authorized': is_authorized})


def edit_project_license(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        if request.method == "POST":
            data = dict(request.POST.items())
            data.pop('csrfmiddlewaretoken')
            project = Project.objects.filter(id=pk).update(**data)

        project = Project.objects.filter(id=pk).values("publish_date", "interpretive_data_license", "identification_information_license", "video_material_license").first()
        return render(request, 'project/edit_project_license.html', {'project': project, 'pk': pk, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk, 'is_authorized': is_authorized})


def edit_project_members(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        # organization_admin
        # if project in organization
        organization_admin = []  # incase there is no one
        organization_id = Organization.objects.filter(projects=pk).values('id')
        for i in organization_id:
            temp = list(Contact.objects.filter(organization=i['id'], is_organization_admin=True).all().values('name', 'email'))
            organization_admin.extend(temp)

        # other members
        members = ProjectMember.objects.filter(project_id=pk).all()

        if request.method == "POST":
            data = dict(request.POST.items())
            # Add member
            if data['action'] == 'add':
                member = Contact.objects.filter(Q(email=data['contact_query']) | Q(orcid=data['contact_query'])).first()
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
                                                                     'organization_admin': organization_admin,
                                                                     'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk, 'is_authorized': is_authorized})


def edit_project_deployment(request, pk):
    is_authorized = check_if_authorized(request, pk)

    if is_authorized:
        project = Project.objects.filter(id=pk)

        study_area = StudyArea.objects.filter(project_id=pk)

        return render(request, 'project/edit_project_deployment.html', {'project': project, 'pk': pk,
                                                                        'study_area': study_area, 'is_authorized': is_authorized})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'project/edit_project_basic.html', {'pk': pk, 'is_authorized': is_authorized})


def get_deployment(request):
    if request.method == "POST":
        id = request.POST.get('study_area_id')

        with connection.cursor() as cursor:
            query = """SELECT id, name, longitude, latitude, altitude, landcover, vegetation, verbatim_locality FROM taicat_deployment WHERE study_area_id = {};"""
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
                                      name=names[i], longitude=longitudes[i], latitude=latitudes[i], altitude=altitudes[i],
                                      landcover=landcovers[i], vegetation=vegetations[i])

        return HttpResponse(json.dumps({'d': 'done'}), content_type='application/json')


def add_studyarea(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        parent_id = request.POST.get('parent_id', None)
        name = request.POST.get('name')

        s = StudyArea.objects.create(name=name, project_id=project_id, parent_id=parent_id)
        data = {'study_area_id': s.id}

        return HttpResponse(json.dumps(data), content_type='application/json')


def get_project_info(project_list):
    with connection.cursor() as cursor:
        q = f"SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                    EXTRACT (year from taicat_project.start_date)::int, \
                    taicat_project.funding_agency \
                    FROM taicat_project \
                    WHERE taicat_project.id IN {project_list} \
                    GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                    ORDER BY taicat_project.start_date DESC;"
        cursor.execute(q)
        project_info = cursor.fetchall()
        project_info = pd.DataFrame(project_info, columns=['id', 'name', 'keyword', 'start_year', 'funding_agency'])
    # count data
    # update if new images
    now = timezone.now()
    last_updated = ProjectStat.objects.filter(project_id__in=list(project_info.id)).aggregate(Min('last_updated'))['last_updated__min']
    has_new = Image.objects.filter(created__gte=last_updated, project_id__in=list(project_info.id))
    if has_new.exists():
        # update project stat
        ProjectStat.objects.filter(project_id__in=list(project_info.id)).update(last_updated=now)
        p_list = has_new.order_by('project_id').distinct('project_id').values_list('project_id', flat=True)
        for i in p_list:
            c = Image.objects.filter(project_id=i).count()
            image_objects = Image.objects.filter(project_id=i, created__gte=last_updated)
            latest_date = image_objects.latest('datetime').datetime
            earliest_date = image_objects.earliest('datetime').datetime
            if ProjectStat.objects.filter(project_id=i).exists():
                p = ProjectStat.objects.get(project_id=i)
                p.num_sa = StudyArea.objects.filter(project_id=i).count()
                p.num_deployment = Deployment.objects.filter(project_id=i).count()
                p.num_data = c
                p.last_updated = now
                if not ProjectStat.objects.get(project_id=i).latest_date or latest_date > ProjectStat.objects.get(project_id=i).latest_date:
                    p.latest_date = latest_date
                if not ProjectStat.objects.get(project_id=i).earliest_date or earliest_date < ProjectStat.objects.get(project_id=i).earliest_date:
                    p.earliest_date = earliest_date
                p.save()
            else:
                p = ProjectStat(
                    project_id=i,
                    num_sa=StudyArea.objects.filter(project_id=i).count(),
                    num_deployment=Deployment.objects.filter(project_id=i).count(),
                    num_data=c,
                    last_updated=now,
                    latest_date=latest_date,
                    earliest_date=earliest_date)
                p.save()
    # update project species
    has_new = Image.objects.filter(last_updated__gte=last_updated, project_id__in=list(project_info.id))
    if has_new.exists():
        p_list = has_new.order_by('project_id').distinct('project_id').values_list('project_id', flat=True)
        ProjectSpecies.objects.filter(project_id__in=list(project_info.id)).update(last_updated=now)
        for i in p_list:
            query = Image.objects.filter(project_id=i).values('species').annotate(total=Count('species')).order_by('-total')
            for q in query:
                if p_sp := ProjectSpecies.objects.filter(name=q['species'], project_id=i).first():
                    p_sp.count = q['total']
                    p_sp.last_updated = now
                    p_sp.save()
                else:
                    q_species = q['species'] if q['species'] else ''
                    if q['total']:
                        p_sp = ProjectSpecies(
                            name=q_species,
                            last_updated=now,
                            count=q['total'],
                            project_id=i)
                        p_sp.save()
    species_data = ProjectSpecies.objects.filter(project_id__in=list(project_info.id), name__in=Species.DEFAULT_LIST).values(
        'name').annotate(total_count=Sum('count')).values_list('total_count', 'name').order_by('-total_count')
    project_info['num_data'] = 0
    project_info['num_studyarea'] = 0
    project_info['num_deployment'] = 0
    for i in project_info.id:
        sa_c = StudyArea.objects.filter(project_id=i).count()
        dep_c = Deployment.objects.filter(project_id=i).count()
        img_c = ProjectStat.objects.get(project_id=i).num_data
        project_info.loc[project_info['id'] == i, 'num_data'] = img_c
        project_info.loc[project_info['id'] == i, 'num_studyarea'] = sa_c
        project_info.loc[project_info['id'] == i, 'num_deployment'] = dep_c
    projects = project_info[['id', 'name', 'keyword', 'start_year', 'funding_agency', 'num_studyarea', 'num_deployment', 'num_data']]
    projects = list(projects.itertuples(index=False, name=None))
    return projects, species_data


def project_overview(request):
    is_authorized_create = check_if_authorized_create(request)
    public_project = []
    public_species_data = []
    # 公開計畫 depend on publish_date date
    with connection.cursor() as cursor:
        q = "SELECT taicat_project.id FROM taicat_project \
            WHERE taicat_project.mode = 'official' AND (CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval);"
        cursor.execute(q)
        public_project_list = [l[0] for l in cursor.fetchall()]
    if public_project_list:
        public_project, public_species_data = get_project_info(str(public_project_list).replace('[', '(').replace(']', ')'))
    # ---------------我的計畫
    # my project
    my_project = []
    my_species_data = []
    my_project_list = []
    if member_id := request.session.get('id', None):
        # 1. select from project_member table
        with connection.cursor() as cursor:
            query = "SELECT project_id FROM taicat_projectmember where member_id ={}"
            cursor.execute(query.format(member_id))
            temp = cursor.fetchall()
            for i in temp:
                if i[0]:
                    my_project_list += [i[0]]
        # 2. check if the user is organization admin
        if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
        if if_organization_admin:
            organization_id = if_organization_admin.values('organization').first()['organization']
            temp = Organization.objects.filter(id=organization_id).values('projects')
            for i in temp:
                my_project_list += [i['projects']]
        if my_project_list:
            my_project, my_species_data = get_project_info(str(my_project_list).replace('[', '(').replace(']', ')'))
    return render(request, 'project/project_overview.html', {'public_project': public_project, 'my_project': my_project, 'is_authorized_create': is_authorized_create,
                                                             'public_species_data': public_species_data, 'my_species_data': my_species_data})


def update_datatable(request):
    # base on species filter
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        species = request.POST.getlist('species[]')
        # print(species)
        if table_id == 'publicproject':
            with connection.cursor() as cursor:
                q = "SELECT taicat_project.id FROM taicat_project \
                    WHERE taicat_project.mode = 'official' AND (CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval);"
                cursor.execute(q)
                public_project_list = [l[0] for l in cursor.fetchall()]
            project_list = ProjectSpecies.objects.filter(name__in=species, project_id__in=public_project_list).order_by('project_id').distinct('project_id')
            project_list = list(project_list.values_list('project_id', flat=True))
        else:
            my_project_list = []
            member_id = request.session.get('id', None)
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
                        project_list = ProjectSpecies.objects.filter(name__in=species, project_id__in=my_project_list).order_by('project_id').distinct('project_id')
                        project_list = list(project_list.values_list('project_id', flat=True))
        project = []
        if project_list:
            project_list = str(project_list).replace('[', '(').replace(']', ')')
            project, _ = get_project_info(project_list)
    return HttpResponse(json.dumps(project), content_type='application/json')


def project_detail(request, pk):
    folder = request.GET.get('folder')
    is_authorized = check_if_authorized(request, pk)
    with connection.cursor() as cursor:
        query = "SELECT name, funding_agency, code, " \
                "principal_investigator, " \
                "to_char(start_date, 'YYYY-MM-DD'), " \
                "to_char(end_date, 'YYYY-MM-DD') FROM taicat_project WHERE id={}"
        cursor.execute(query.format(pk))
        project_info = cursor.fetchone()
    project_info = list(project_info)
    deployment = Deployment.objects.filter(project_id=pk)
    # folder name takes long time
    # folder_list = Image.objects.filter(project_id=pk).order_by('folder_name').distinct('folder_name')
    now = timezone.now()
    last_updated = ProjectStat.objects.filter(project_id=pk).aggregate(Min('last_updated'))['last_updated__min']
    has_new = Image.objects.filter(created__gte=last_updated, project_id=pk)
    if has_new.exists():
        # update project stat
        ProjectStat.objects.filter(project_id=pk).update(last_updated=now)
        c = Image.objects.filter(project_id=pk).count()
        image_objects = Image.objects.filter(project_id=pk, created__gte=last_updated)
        latest_date = image_objects.latest('datetime').datetime
        earliest_date = image_objects.earliest('datetime').datetime
        if ProjectStat.objects.filter(project_id=pk).exists():
            p = ProjectStat.objects.get(project_id=pk)
            p.num_sa = StudyArea.objects.filter(project_id=pk).count()
            p.num_deployment = Deployment.objects.filter(project_id=pk).count()
            p.num_data = c
            p.last_updated = now
            if not ProjectStat.objects.get(project_id=pk).latest_date or latest_date > ProjectStat.objects.get(project_id=pk).latest_date:
                p.latest_date = latest_date
            if not ProjectStat.objects.get(project_id=pk).earliest_date or earliest_date < ProjectStat.objects.get(project_id=pk).earliest_date:
                p.earliest_date = earliest_date
            p.save()
        else:
            p = ProjectStat(
                project_id=pk,
                num_sa=StudyArea.objects.filter(project_id=pk).count(),
                num_deployment=Deployment.objects.filter(project_id=pk).count(),
                num_data=c,
                last_updated=now,
                latest_date=latest_date,
                earliest_date=earliest_date)
            p.save()
    # update project species
    has_new = Image.objects.filter(last_updated__gte=last_updated, project_id=pk)
    if has_new.exists():
        ProjectSpecies.objects.filter(project_id=pk).update(last_updated=now)
        query = Image.objects.filter(project_id=pk).values('species').annotate(total=Count('species')).order_by('-total')
        for q in query:
            # print(q['species'], q['total'])
            if p_sp := ProjectSpecies.objects.filter(name=q['species'], project_id=pk).first():
                p_sp.count = q['total']
                p_sp.last_updated = now
                p_sp.save()
            else:
                q_species = q['species'] if q['species'] else ''
                if q['total']:
                    p_sp = ProjectSpecies(
                        name=q_species,
                        last_updated=now,
                        count=q['total'],
                        project_id=pk)
                    p_sp.save()
    # update imagefolder table
    has_new = Image.objects.exclude(folder_name='').filter(last_updated__gte=last_updated, project_id=pk)
    if has_new.exists():
        ImageFolder.objects.filter(project_id=pk).update(last_updated=now)
        query = Image.objects.exclude(folder_name='').filter(last_updated__gte=last_updated, project_id=pk).order_by('folder_name').distinct('folder_name').values('folder_name')
        for q in query:
            f_last_updated = Image.objects.filter(last_updated__gte=last_updated, project_id=pk, folder_name=q['folder_name']).aggregate(Max('last_updated'))['last_updated__max']
            if img_f := ImageFolder.objects.filter(name=q['folder_name'], project_id=pk).first():
                img_f.folder_last_updated = f_last_updated
                img_f.last_updated = now
                img_f.save()
            else:
                img_f = ImageFolder(
                    folder_name=q['folder_name'],
                    folder_last_updated=f_last_updated,
                    project_id=pk)
                img_f.save()

    species = ProjectSpecies.objects.filter(project_id=pk).values_list('count', 'name').order_by('count')

    if ProjectStat.objects.filter(project_id=pk).first().latest_date and ProjectStat.objects.filter(project_id=pk).first().earliest_date:
        latest_date = ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d")
        earliest_date = ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")
    else:
        latest_date, earliest_date = None, None

    with connection.cursor() as cursor:
        query = f"""SELECT folder_name,
                        to_char(last_updated AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS last_updated
                        FROM taicat_imagefolder
                        WHERE project_id = {pk}"""
        cursor.execute(query)
        folder_list = cursor.fetchall()
        columns = list(cursor.description)
        results = []
        for row in folder_list:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col.name] = row[i]
            results.append(row_dict)
    # edit permission
    user_id = request.session.get('id', None)
    editable = False
    if user_id:
        # 系統管理員 / 個別計畫承辦人
        if Contact.objects.filter(id=user_id, is_system_admin=True).first() or ProjectMember.objects.filter(member_id=user_id, role="project_admin", project_id=pk):
            editable = True
        # 計畫總管理人
        elif Contact.objects.filter(id=user_id, is_organization_admin=True):
            organization_id = Contact.objects.filter(id=user_id, is_organization_admin=True).values('organization').first()['organization']
            if Organization.objects.filter(id=organization_id, projects=pk):
                editable = True
    study_area = StudyArea.objects.filter(project_id=pk).order_by('name')
    sa_list = Project.objects.get(pk=pk).get_sa_list()
    sa_d_list = Project.objects.get(pk=pk).get_sa_d_list()
    return render(request, 'project/project_detail.html',
                  {'project_name': len(project_info[0]), 'project_info': project_info, 'species': species, 'pk': pk,
                   'study_area': study_area, 'deployment': deployment, 'folder': folder,
                   'earliest_date': earliest_date, 'latest_date': latest_date,
                   'editable': editable, 'is_authorized': is_authorized,
                   'folder_list': results, 'sa_list': list(sa_list), 'sa_d_list': sa_d_list})


def data(request):
    t = time.time()
    requests = request.POST
    pk = requests.get('pk')
    _start = requests.get('start')
    _length = requests.get('length')

    start_date = requests.get('start_date')
    end_date = requests.get('end_date')
    date_filter = ''
    if ((start_date and start_date != ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")) or (end_date and end_date != ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"))):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = "AND datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)
    conditions = ''
    deployment = requests.getlist('deployment[]')
    sa = requests.get('sa')
    if sa:
        conditions += f'AND studyarea_id = {sa}'
        if deployment:
            if 'all' not in deployment:
                x = [int(i) for i in deployment]
                x = str(x).replace('[', '(').replace(']', ')')
                conditions += f'AND deployment_id IN {x}'
        else:
            conditions = 'AND deployment_id IS NULL'
    spe_conditions = ''
    species = requests.getlist('species[]')
    if species:
        if 'all' not in species:
            x = [i for i in species]
            x = str(x).replace('[', '(').replace(']', ')')
            spe_conditions = f"AND species IN {x}"

    time_filter = ''  # 要先減掉8的時差
    if times := requests.get('times'):
        result = datetime.datetime.strptime(f"1990-01-01 {times}", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=-8)
        time_filter = f"AND datetime::time AT TIME ZONE 'UTC' = time '{result.strftime('%H:%M:%S')}'"

    folder_filter = ''
    if folder_name := requests.get('folder_name'):
        folder_filter = f"AND folder_name = '{folder_name}'"

    with connection.cursor() as cursor:
        query = """SELECT id, studyarea_id, deployment_id, filename, species,
                        life_stage, sex, antler, animal_id, remarks, file_url, image_uuid, from_mongo,
                        to_char(datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime
                        FROM taicat_image
                        WHERE project_id = {} {} {} {} {} {}
                        ORDER BY created DESC, project_id ASC
                        LIMIT {} OFFSET {}"""
        # set limit = 1000 to avoid bad psql query plan
        cursor.execute(query.format(pk, date_filter, conditions, spe_conditions, time_filter, folder_filter, 1000, _start))
        image_info = cursor.fetchall()
        print(query.format(pk, date_filter, conditions, spe_conditions, time_filter, folder_filter, 1000, _start))
    if image_info:

        df = pd.DataFrame(image_info, columns=['image_id', 'studyarea_id', 'deployment_id', 'filename', 'species', 'life_stage', 'sex', 'antler',
                                               'animal_id', 'remarks', 'file_url', 'image_uuid', 'from_mongo', 'datetime'])[:int(_length)]
        print('b', time.time()-t)
        sa_names = pd.DataFrame(StudyArea.objects.filter(id__in=df.studyarea_id.unique()).values('id', 'name', 'parent_id')
                                ).rename(columns={'id': 'studyarea_id', 'name': 'saname', 'parent_id': 'saparent'})
        d_names = pd.DataFrame(Deployment.objects.filter(id__in=df.deployment_id.unique()).values('id', 'name')).rename(columns={'id': 'deployment_id', 'name': 'dname'})
        df = df.merge(d_names).merge(sa_names)

        with connection.cursor() as cursor:
            query = """SELECT COUNT(*)
                            FROM taicat_image i
                            WHERE project_id = {} {} {} {} {} {}"""
            cursor.execute(query.format(pk, date_filter, conditions, spe_conditions, time_filter, folder_filter))
            count = cursor.fetchone()
        recordsTotal = count[0]

        print('c-1', time.time()-t)
        recordsFiltered = recordsTotal

        start = int(_start)
        length = int(_length)
        per_page = length
        page = math.ceil(start / length) + 1
        # add sub studyarea if exists
        ssa_exist = StudyArea.objects.filter(project_id=pk, parent__isnull=False)
        if ssa_exist.count() > 0:
            ssa_list = list(ssa_exist.values_list('name', flat=True))
            for i in df[df.saname.isin(ssa_list)].index:
                try:
                    parent_saname = StudyArea.objects.get(id=df.saparent[i]).name
                    current_name = df.saname[i]
                    df.loc[i, 'saname'] = f"{parent_saname}_{current_name}"
                except:
                    pass
        print('d', time.time()-t)

        # if 花蓮 test -> camera-trap-21-prod; else -> camera-trap-21
        s3_bucket = 'camera-trap-21-prod' if pk == 330 else 'camera-trap-21'

        for i in df.index:
            file_url = df.file_url[i]
            # 嘉大助理test
            s3_bucket = 'camera-trap-21-prod' if df.memo[i] == '2022-pt-data' else s3_bucket
            if not file_url and not df.from_mongo[i]:
                file_url = f"{df.image_id[i]}-m.jpg"
            extension = file_url.split('.')[-1].lower()
            file_url = file_url[:-len(extension)]+extension
            # print(file_url)
            if not df.from_mongo[i]:
                # new data - image
                if extension in ['jpg', '']:
                    df.loc[i, 'file_url'] = """<img class="img lazy mx-auto d-block" style="height: 100px" data-src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" />""".format(s3_bucket, file_url)
                # new data - video
                else:
                    df.loc[i, 'file_url'] = """
                    <video class="img lazy mx-auto d-block" controls height="100" preload="none">
                        <source src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" type="video/webm">
                        <source src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" type="video/mp4">
                        抱歉，您的瀏覽器不支援內嵌影片。
                    </video>
                    """.format(s3_bucket, file_url, s3_bucket, file_url)
            else:
                # old data - image
                if extension in ['jpg', '']:
                    df.loc[i, 'file_url'] = """<img class="img lazy mx-auto d-block" style="height: 100px" data-src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{}" />""".format(
                        file_url)
                # old data - video
                else:
                    df.loc[i, 'file_url'] = """
                    <video class="img lazy mx-auto d-block" controls height="100" preload="none">
                        <source src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-videos/{}" type="video/webm">
                        <source src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-videos/{}" type="video/mp4">
                        抱歉，您的瀏覽器不支援內嵌影片。
                    </video>
                    """.format(file_url, file_url)
            ### videos: https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/video ##
        print('e', time.time()-t)

        df['edit'] = df.image_id.apply(lambda x: f"<input type='checkbox' class='edit-checkbox' name='edit' value='{x}'>")

        cols = ['edit', 'saname', 'dname', 'filename', 'datetime', 'species', 'lifestage',
                'sex', 'antler', 'animal_id', 'remarks', 'file_url', 'image_uuid', 'image_id']
        data = df.reindex(df.columns.union(cols, sort=False), axis=1, fill_value=None)
        data = data[cols]
        data = data.astype(object).replace(np.nan, '')
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


def download_request(request, pk):
    task = threading.Thread(target=generate_download_excel, args=(request, pk))
    # task.daemon = True
    task.start()
    return JsonResponse({"status": 'success'}, safe=False)


def generate_download_excel(request, pk):
    requests = request.POST
    email = requests.get('email', '')
    start_date = requests.get('start_date')
    end_date = requests.get('end_date')
    date_filter = ''
    if ((start_date and start_date != ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")) or (end_date and end_date != ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"))):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = "AND datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)

    conditions = ''
    deployment = requests.getlist('d-filter')
    sa = requests.get('sa-filter')
    if sa:
        conditions += f' AND studyarea_id = {sa}'
        if deployment:
            if 'all' not in deployment:
                x = [int(i) for i in deployment]
                x = str(x).replace('[', '(').replace(']', ')')
                conditions += f' AND deployment_id IN {x}'
        else:
            conditions = ' AND deployment_id IS NULL'
    spe_conditions = ''
    species = requests.getlist('species-filter')
    if species:
        if 'all' not in species:
            x = [i for i in species]
            x = str(x).replace('[', '(').replace(']', ')')
            spe_conditions = f" AND species IN {x}"

    time_filter = ''  # 要先減掉8的時差
    if times := requests.get('times'):
        result = datetime.datetime.strptime(f"1990-01-01 {times}", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=-8)
        time_filter = f" AND datetime::time AT TIME ZONE 'UTC' = time '{result.strftime('%H:%M:%S')}'"

    folder_filter = ''
    if folder_name := requests.get('folder_name'):
        folder_filter = f"AND folder_name = '{folder_name}'"

    with connection.cursor() as cursor:
        query = f"""SELECT studyarea_id, deployment_id, filename, species,
                        life_stage, sex, antler, animal_id, remarks, file_url, image_uuid, from_mongo, 
                        to_char(datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime
                        FROM taicat_image 
                        WHERE project_id = {pk} {date_filter} {conditions} {spe_conditions} {time_filter} {folder_filter}
                        ORDER BY created DESC, project_id ASC"""
        cursor.execute(query)
        image_info = cursor.fetchall()

    if image_info:
        df = pd.DataFrame(image_info, columns=['studyarea_id', 'deployment_id', 'filename', 'species', 'life_stage', 'sex', 'antler',
                                               'animal_id', 'remarks', 'file_url', 'image_uuid', 'from_mongo', 'datetime'])
        sa_names = pd.DataFrame(StudyArea.objects.filter(id__in=df.studyarea_id.unique()).values('id', 'name', 'parent_id')
                                ).rename(columns={'id': 'studyarea_id', 'name': 'saname', 'parent_id': 'saparent'})
        d_names = pd.DataFrame(Deployment.objects.filter(id__in=df.deployment_id.unique()).values('id', 'name')).rename(columns={'id': 'deployment_id', 'name': 'dname'})
        df = df.merge(d_names).merge(sa_names)
        df = df.reset_index()

        # add sub studyarea if exists
        df['subsaname'] = ''
        ssa_exist = StudyArea.objects.filter(project_id=pk, parent__isnull=False)
        if ssa_exist.count() > 0:
            ssa_list = list(ssa_exist.values_list('name', flat=True))
            for i in df[df.saname.isin(ssa_list)].index:
                try:
                    parent_saname = StudyArea.objects.get(id=df.saparent[i]).name
                    current_name = df.saname[i]
                    df.loc[i, 'saname'] = f"{parent_saname}"
                    df.loc[i, 'subsaname'] = f"{current_name}"
                except:
                    pass

        df['計畫名稱'] = Project.objects.get(id=pk).name
        df['計畫ID'] = pk
        # rename
        df = df.rename(columns={'saname': '樣區', 'dname': '相機位置', 'filename': '檔名', 'datetime': '拍攝時間', 'species': '物種',
                                'lifestage': '年齡', 'sex': '性別', 'antler': '角況', 'remarks': '備註', 'animal_id': '個體ID', 'image_uuid': '影像ID',
                                'subsaname': '子樣區'})
        # subset and change column order
        cols = ['計畫ID', '計畫名稱', '影像ID', '樣區', '子樣區', '相機位置',
                '檔名', '拍攝時間', '物種', '年齡', '性別', '角況', '個體ID', '備註']
        for i in cols:
            if i not in df:
                df[i] = ''
        df = df[cols]

    else:
        df = pd.DataFrame()  # no data

    n = f'download_{randomword(8)}_{datetime.datetime.now().strftime("%Y-%m-%d")}.xlsx'

    download_dir = os.path.join(settings.MEDIA_ROOT, 'download')
    df.to_excel(os.path.join(download_dir, n), index=False)
    download_url = request.scheme+"://" + \
        request.META['HTTP_HOST']+settings.MEDIA_URL + \
        os.path.join('download', n)
    if settings.ENV == 'prod':
        download_url = download_url.replace('http', 'https')

    email_subject = '[臺灣自動相機資訊系統] 下載資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])
    # return response


def project_oversight(request, pk):
    '''
    相機有運作天數 / 當月天數
    '''
    if request.method == 'GET':
        is_authorized = check_if_authorized(request, pk)
        public_ids = Project.published_objects.values_list(
            'id', flat=True).all()
        pk = int(pk)
        if (pk in list(public_ids)) or is_authorized:
            project = Project.objects.get(pk=pk)

            # min/max 超慢?
            mnx = Image.objects.filter(project_id=pk).aggregate(
                Max('datetime'), Min('datetime'))
            # print(mnx)
            year = request.GET.get('year')
            end_year = mnx['datetime__max'].year
            start_year = mnx['datetime__min'].year
            year_list = list(range(start_year, end_year+1))
            # imax = Image.objects.values('datetime').filter(project_id=pk).order_by('datetime')[:1]
            # imin = Image.objects.filter(project_id=pk).order_by('-datetime')[:1]
            # print(imax)
            # print(mn.first(), mn.last())
            # year_list = list(range(2010, 2022))

            result = []
            if year:
                year = int(year)
                deps = project.get_deployment_list()
                for sa in deps:
                    items_d = []
                    for d in sa['deployments']:
                        dep_id = d['deployment_id']
                        month_list = []
                        for m in range(1, 13):
                            days_in_month = monthrange(year, m)[1]
                            ret = find_deployment_working_day(year, m, dep_id)
                            working_day = ret[0]
                            # print(year, m, dep_id, working_day)
                            # display_day_list = ['{}:{}'.format(index+1, 'Y' if yes else 'N') for index, yes in enumerate(working_day)]
                            month_cal = monthcalendar(year, m)
                            # display_working_day_in_calendar(year, m, working_day)
                            count_working_day = sum(working_day)
                            data = [
                                year,
                                m,
                                d['name'],
                                count_working_day,
                                days_in_month,
                                month_cal,
                                working_day,
                                ret[1],
                            ]
                            ratio = count_working_day * 100.0 / days_in_month
                            month_list.append([ratio, json.dumps(data)])
                        # query = Image.objects.values('datetime').filter(project_id=pk, deployment_id=dep_id).annotate(year=Trunc('datetime', 'year')).filter(datetime__year=year).annotate(day=Trunc('datetime', 'day')).annotate(count=Count('day'))
                        # print(query.query)

                        # with connection.cursor() as cursor:
                        #    query = f"SELECT DATE_TRUNC('day', datetime) AS day FROM taicat_image WHERE deployment_id={dep_id} AND datetime BETWEEN '{year}-01-01' AND '{year}-12-31' GROUP BY day ORDER BY day;"
                        #    cursor.execute(query)
                        #    data = cursor.fetchall()
                        #    for i in data:
                        #        month_idx = i[0].month - 1
                        #        month_list[month_idx][1][0] += 1
                        #        month_list[month_idx][0] = month_list[month_idx][1][0] * \
                        #            100.0 / month_list[month_idx][1][1]
                        items_d.append({
                            'name': d['name'],
                            'items': month_list,
                        })
                    result.append({
                        'name': sa['name'],
                        'items': items_d
                    })
                    # print(result)

            return render(request, 'project/project_oversight.html', {
                'project': project,
                'year_list': year_list,
                'month_label_list': [f'{x} 月'for x in range(1, 13)],
                'result': result,
            })
        else:
            return ''
