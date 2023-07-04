from curses import flash
from django.db.models.fields import PositiveBigIntegerField
from django.http import (
    response,
    JsonResponse,
    StreamingHttpResponse,
)
from django.core.serializers import serialize
from django.shortcuts import redirect, render, HttpResponse
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from pandas.core.groupby.generic import DataFrameGroupBy
from taicat.models import *
from base.models import UploadNotification
from django.db import connection  # for executing raw SQL
import re
import json
import math
import datetime
from tempfile import NamedTemporaryFile
from urllib.parse import quote
# from datetime import datetime, timedelta, timezone
from pathlib import Path
from django.db.models import Count, Window, F, Sum, Min, Q, Max, Func, Value, CharField, DateTimeField, ExpressionWrapper
from django.db.models.functions import Trunc, ExtractYear
from django.contrib import messages
from django.core import serializers
import pandas as pd
from decimal import Decimal
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
#from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from base.utils import generate_token, update_studyareastat
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
    find_deployment_working_day,
    get_my_project_list
)
import collections
from operator import itemgetter
from dateutil import parser
from django.test.utils import CaptureQueriesContext
from base.utils import DecimalEncoder
from taicat.utils import half_year_ago, get_project_member, delete_image_by_ids

from openpyxl import Workbook
from bson.objectid import ObjectId
import geopandas as gpd
from shapely.geometry import Point
from django.views.decorators.http import require_GET



def get_project_info_web(request):
    pk = request.GET.get('pk')
    # 系統管理員
    member_id = request.session.get('id', None)
    is_authorized = Contact.objects.filter(id=member_id, is_system_admin=True).exists()
    
    # 團隊成員名單
    pm_list = get_project_member(pk)
    if (member_id in pm_list) or is_authorized:
        is_project_authorized = True
    else:
        is_project_authorized = False
        
    response = {}
    project = Project.objects.get(id=pk)
    sa = StudyArea.objects.filter(project_id=pk, parent_id__isnull=True)
    sa_list = [str(s.id) for s in sa]
    response['sa_list'] = sa_list
    sa_center = [23.5, 121.2]
    zoom = 6
    if sa:
        sa_point = Deployment.objects.filter(study_area_id__in=sa_list, latitude__isnull = False, longitude__isnull = False).order_by('-latitude').values('latitude','longitude','geodetic_datum').first()
        if sa_point:
            if sa_point['geodetic_datum'] == 'WGS84':
                sa_center = [float(sa_point['latitude']),float(sa_point['longitude'])]
            else:
                df = pd.DataFrame({
                            'Lat':[int(sa_point['latitude'])],
                            'Lon':[int(sa_point['longitude'])]})

                geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
                gdf = gpd.GeoDataFrame(df, geometry=geometry)

                gdf = gdf.set_crs(epsg=3826, inplace=True)
                gdf = gdf.to_crs(epsg=4326)
                sa_center = [gdf.geometry.y[0],gdf.geometry.x[0]]
            zoom = 8

    species_count = 0
    species_last_updated = None

    query = f"select sum(count) from taicat_projectspecies where project_id={pk};"
    with connection.cursor() as cursor:
        cursor.execute(query)
        species_total_count = cursor.fetchall()
        species_total_count = species_total_count[0][0]

    pie_data = []
    others = {'name': '其他物種', 'count': 0, 'y': 0}
    other_data = []
    # 取前8名，剩下的統一成其他
    if species_total_count:
        if ProjectSpecies.objects.filter(project_id=pk).exists():
            species_count = ProjectSpecies.objects.filter(project_id=pk).exclude(name='').values('name').distinct().count()
            species_last_updated = ProjectSpecies.objects.filter(project_id=pk).annotate(
                last_updated_8=ExpressionWrapper(
                    F('last_updated') + timedelta(hours=8),
                    output_field=DateTimeField()
                )).latest('last_updated_8').last_updated_8
            c = 0
            for i in ProjectSpecies.objects.filter(project_id=pk).order_by('-count'):
                s_name = '未填寫' if i.name == '' else i.name
                c += 1
                if c < 9:
                    pie_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                else:
                    if is_project_authorized:
                        other_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                        others.update({'count': others['count']+i.count})
                    else:
                        if not re.search("人",s_name):
                            other_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                            others.update({'count': others['count']+i.count})
                        
            if others['count'] > 0:
                others.update({'y': round(others['count']/species_total_count*100, 2)})
                pie_data += [others]
    response['pie_data'] = pie_data
    response['other_data'] = other_data
    response['zoom'] = zoom
    response['sa_point'] = sa_center
    response['species_count'] = species_count
    response['species_last_updated'] = species_last_updated.strftime("%Y-%m-%d") if species_last_updated else species_last_updated

    return HttpResponse(json.dumps(response), content_type='application/json')


def get_edit_info(request):

    type = request.GET.get('type')
    pk = request.GET.get('pk')
    response = {}
    if type == 'license':
        response = Project.objects.filter(id=pk).values("interpretive_data_license", "identification_information_license", "video_material_license").first()
    elif type == 'basic':
        project = Project.objects.filter(id=pk).values('region').first()
        if project['region'] not in ['', None, []]:
            response = {'region': project['region'].split(',')}
    elif type == 'deployment':
        response['study_area'] = list(StudyArea.objects.filter(project_id=pk).values("id","parent_id","name"))
    elif type == 'members':
        response['members'] = list( ProjectMember.objects.filter(project_id=pk).values("member_id","role"))


    return HttpResponse(json.dumps(response), content_type='application/json')


def get_project_detail(request):
    pk = request.GET.get('pk')
    response = {}
    if ProjectStat.objects.filter(project_id=pk).first().latest_date and ProjectStat.objects.filter(project_id=pk).first().earliest_date:
        latest_date = ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d")
        earliest_date = ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")
    else:
        latest_date, earliest_date = None, None

    
    results = []
    with connection.cursor() as cursor:
        query = f"""SELECT folder_name,
                        to_char(folder_last_updated AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS folder_last_updated
                        FROM taicat_imagefolder
                        WHERE project_id = {pk}
                        ORDER BY folder_last_updated desc"""
        cursor.execute(query)
        folder_list = cursor.fetchall()
        columns = list(cursor.description)
        for row in folder_list:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col.name] = row[i]
            results.append(row_dict)
    response['folder_list'] = results
    response['latest_date'] = latest_date
    response['earliest_date'] = earliest_date
    response['sa_d_list'] = Project.objects.get(pk=pk).get_sa_d_list()
    response['sa_list'] = Project.objects.get(pk=pk).get_sa_list()
    
    # altitude_range = Deployment.objects.filter(project_id=pk,deprecated=False).aggregate(Max("altitude"), Min("altitude"))
    # response['altitude__max'] = altitude_range['altitude__max']
    # response['altitude__min'] = altitude_range['altitude__min']
    
    study_area = []
    for sa in StudyArea.objects.filter(project_id=pk).order_by('name'):
        d_list = []
        for d in sa.deployment_set.all():
            d_list.append({'id': d.id, 'name': d.name})
        study_area.append({'id': sa.id, 'parent_id': sa.parent_id, 'name': sa.name, 'deployment_set': d_list})
    response['study_area'] = study_area
    
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
    if editable:
        pid_list = get_my_project_list(user_id,[])
        projects = Project.objects.filter(pk__in=pid_list)
        project_list = []
        for p in projects:
            project_list += [{'label': p.name, 'value': p.id}]
    else:
        project_list = []
    response['projects'] = project_list

    
    response['editable'] = editable
    return HttpResponse(json.dumps(response), content_type='application/json')


def update_species_map(request):

    # 根據filter (樣區,子樣區, 行程) 更新物種地圖
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    date_filter = ''
    if (start_date and end_date):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = " AND i.datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)
    elif start_date:
        date_filter = " AND i.datetime > '{}'".format(start_date)
    elif end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = " AND i.datetime < '{}'".format(start_date)

    species = request.GET.get('species')
    
    if species == '未填寫':
        species = ''
    # print(date_filter)

    data = []
    new_data = []

    if sa := request.GET.get('said'):
        type = '相機位置'
        # 確定有沒有子樣區
        subsa = StudyArea.objects.filter(parent_id=sa)
        sa_list = [str(s.id) for s in subsa]
        if sa_list:
            query = f"""
                    SELECT COUNT(*), d.longitude, d.latitude, d.name, d.geodetic_datum FROM taicat_image i 
                    JOIN taicat_deployment d ON i.deployment_id = d.id
                    WHERE i.species='{species}' AND i.studyarea_id IN ({','.join(sa_list)})"""
        else:
            query = f"""
                    SELECT COUNT(*), d.longitude, d.latitude, d.name, d.geodetic_datum FROM taicat_image i 
                    JOIN taicat_deployment d ON i.deployment_id = d.id
                    WHERE i.species='{species}' AND i.studyarea_id={sa}"""
    elif pk := request.GET.get('said[project]'):
        type = '樣區'
        # 抓樣區中心點 group by 樣區
        sas = StudyArea.objects.filter(project_id=pk)
        sa_list = [str(s.id) for s in sas]
        # sa = StudyAreaStat.objects.filter(studyarea_id__in=sa_list)
        if sa_list:
            if last_updated := StudyAreaStat.objects.filter(studyarea_id__in=sa_list).aggregate(Min('last_updated'))['last_updated__min']:
            # has_new = Deployment.objects.filter(last_updated__gte=last_updated, study_area_id__in=sa_list).exists()
                if Deployment.objects.filter(last_updated__gte=last_updated, study_area_id__in=sa_list).exists():
                    update_studyareastat(','.join(sa_list))
            else:
                update_studyareastat(','.join(sa_list))
            query = f"""
                    SELECT COUNT(*), sas.longitude, sas.latitude, sa.name, '' FROM taicat_image i 
                    JOIN taicat_studyareastat sas ON i.studyarea_id = sas.studyarea_id
                    JOIN taicat_studyarea sa ON i.studyarea_id = sa.id
                    WHERE i.species='{species}' AND i.studyarea_id IN ({','.join(sa_list)})"""
    if query:
        if date_filter:
            query += date_filter

        with connection.cursor() as cursor:
            if sa:
                query += ' group by i.deployment_id, d.longitude, d.latitude, d.name, d.geodetic_datum'
            elif pk:
                query += ' group by i.studyarea_id, sas.longitude, sas.latitude, sa.name'
            cursor.execute(query)
            data = cursor.fetchall()
            for d in data:
                if d[4] == 'TWD97':
                    df = pd.DataFrame({
                                'Lat':[int(d[2])],
                                'Lon':[int(d[1])]})
                    geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
                    gdf = gpd.GeoDataFrame(df, geometry=geometry)
                    gdf = gdf.set_crs(epsg=3826, inplace=True)
                    gdf = gdf.to_crs(epsg=4326)
                    new_data.append((d[0], gdf.geometry.x[0], gdf.geometry.y[0], d[3]))
                    # sa_center = [gdf.geometry.y[0],gdf.geometry.x[0]]
                else:
                    new_data.append((d[0], d[1], d[2], d[3]))

    last_updated = timezone.now() + timedelta(hours=8)
    last_updated = datetime.datetime.strftime(last_updated,'%Y-%m-%d') 

    total_count = 0
    for d in new_data:
        total_count += d[0]

    response = {'data': new_data, 'last_updated': last_updated, 'total_count': total_count, 'type': type}

    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')
    


def edit_sa(request):
    if request.method == 'GET':
        name = request.GET.get('name')
        id = request.GET.get('id')
        StudyArea.objects.filter(id=id).update(name = name)
        response = {'status': 'done'}
        return HttpResponse(json.dumps(response), content_type='application/json')


def delete_dep_sa(request):
    if request.method == 'GET':
        type = request.GET.get('type')
        id = request.GET.get('id')
        project_id = request.GET.get('project_id')
        response = {}
        if type == 'sa':
            if Image.objects.filter(studyarea_id=id).exists():
                response = {'status': 'exists'}
            # StudyArea.objects.filter(id=id).delete()
            else:
                StudyArea.objects.filter(id=id).delete()
                # 修改樣區數量
                if ProjectStat.objects.filter(project_id=project_id).exists():
                    ProjectStat.objects.filter(project_id=project_id).update(num_sa = StudyArea.objects.filter(project_id=project_id).count())
                response = {'status': 'done'}
        elif type =='dep':
            if Image.objects.filter(deployment_id=id).exists():
                response = {'status': 'exists'}
            else:
                Deployment.objects.filter(id=id).delete()
                # 修改相機位置數量 
                if ProjectStat.objects.filter(project_id=project_id).exists():
                    ProjectStat.objects.filter(project_id=project_id).update(num_deployment = Deployment.objects.filter(project_id=project_id).count())
                response = {'status': 'done'}
        # response = {'d': 'done'}
        return HttpResponse(json.dumps(response), content_type='application/json')

def get_sa_points(request):
    sa_list = request.GET.getlist('sa[]')
    sa_points = []
    if sa_list:
        if last_updated := StudyAreaStat.objects.filter(studyarea_id__in=sa_list).aggregate(Min('last_updated'))['last_updated__min']:
            if Deployment.objects.filter(last_updated__gte=last_updated, study_area_id__in=sa_list).exists():
                update_studyareastat(','.join(sa_list))
        else:
            update_studyareastat(','.join(sa_list))

        with connection.cursor() as cursor:
            query = f"""SELECT sas.longitude, sas.latitude, sa.name, sa.id  
                        FROM taicat_studyareastat sas  
                        JOIN taicat_studyarea sa ON sas.studyarea_id = sa.id
                        WHERE sas.studyarea_id IN ({','.join(sa_list)});"""
            cursor.execute(query)
            sa_points = cursor.fetchall()
        
    response = {'sa_points': sa_points}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_subsa(request):
    # 取得子樣區及行程列表
    said = request.GET.get('said')
    subsas = []
    if said:
        with connection.cursor() as cursor:
            query = f"""SELECT id, name
                        FROM taicat_studyarea   
                        WHERE parent_id = {said};"""
            cursor.execute(query)
            subsas = cursor.fetchall()
        
    response = {'subsas': subsas}
    return HttpResponse(json.dumps(response), content_type='application/json')


def update_species_pie(request):

    # 根據filter (樣區,子樣區, 行程) 更新物種圓餅圖
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    date_filter = ''
    if (start_date and end_date):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = " AND datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)
    elif start_date:
        date_filter = " AND datetime > '{}'".format(start_date)
    elif end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = " AND datetime < '{}'".format(end_date)

    # print(date_filter)

    species_count = 0
    species_last_updated = None
    species_total_count = 0
    pie_data = []
    other_data = []
    deployment_points = []
    new_deployment_points = []
    if sa := request.GET.get('said'):
        # 確定有沒有子樣區
        subsa = StudyArea.objects.filter(parent_id=sa)
        sa_list = [str(s.id) for s in subsa]
        # pie data
        if sa_list:
            query = f"select count(*) from taicat_image where studyarea_id IN ({','.join(sa_list)})"
        else:
            query = f"select count(*) from taicat_image where studyarea_id={sa}"
        if date_filter:
            query += date_filter
        with connection.cursor() as cursor:
            cursor.execute(query)
            species_total_count = cursor.fetchall()
            species_total_count = species_total_count[0][0]

        others = {'name': '其他物種', 'count': 0, 'y': 0}
        # 取前8名，剩下的統一成其他
        if species_total_count:
            species_last_updated = timezone.now() + timedelta(hours=8)
            species_last_updated = datetime.datetime.strftime(species_last_updated,'%Y-%m-%d') 
            pre_q = Image.objects
            if sa_list:
                pre_q = pre_q.filter(studyarea_id__in=sa_list)
            else:
                pre_q = pre_q.filter(studyarea_id=sa)
            if start_date:
                pre_q = pre_q.filter(datetime__gte=start_date)
            if end_date:
                pre_q = pre_q.filter(datetime__lt=end_date)

            query = pre_q.values('species').annotate(total=Count('species')).order_by('-total')
            c = 0
            for i in query:
                if i['species'] == '':
                    s_name = '未填寫'
                else:
                    s_name = i['species']
                    species_count += 1
                c += 1
                if c < 9:
                    pie_data += [{'name': s_name, 'y': round(i['total']/species_total_count*100, 2), 'count': i['total']}]
                else:
                    other_data += [{'name': s_name, 'y': round(i['total']/species_total_count*100, 2), 'count': i['total']}]
                    others.update({'count': others['count']+i['total']})
            if others['count'] > 0:
                others.update({'y': round(others['count']/species_total_count*100, 2)})
                pie_data += [others]

        # deployments
        if sa_list:
            # 抓子樣區 & 該樣區底下的相機位置
            # SAS裡面已經都是WGS84
            query = f"""SELECT sas.longitude, sas.latitude, sa.name, TRUE as sub, sa.id, 'WGS84' FROM taicat_studyareastat sas
                        JOIN taicat_studyarea sa ON sas.studyarea_id = sa.id
                        WHERE sas.studyarea_id IN ({','.join(sa_list)}) 
                        UNION 
                        SELECT longitude, latitude, name, FALSE as sub, study_area_id, geodetic_datum FROM taicat_deployment WHERE study_area_id = {sa} 
                        ORDER BY longitude DESC;"""
        else:
            query = f"""SELECT longitude, latitude, name, FALSE as sub, study_area_id, geodetic_datum FROM taicat_deployment WHERE study_area_id = {sa} ORDER BY longitude DESC;"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            deployment_points = cursor.fetchall()
            
            for d in deployment_points:
                if d[5] == 'TWD97':
                    df = pd.DataFrame({
                                'Lat':[int(d[1])],
                                'Lon':[int(d[0])]})
                    geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
                    gdf = gpd.GeoDataFrame(df, geometry=geometry)
                    gdf = gdf.set_crs(epsg=3826, inplace=True)
                    gdf = gdf.to_crs(epsg=4326)
                    new_deployment_points.append((gdf.geometry.x[0], gdf.geometry.y[0], d[2], d[3], d[4], d[5]))
                else:
                    new_deployment_points.append(d)
            
    elif pk := request.GET.get('said[project]'):
        deployment_points = []
        query = f"select count(*) from taicat_image where project_id={pk}"
        if date_filter:
            query += date_filter
        with connection.cursor() as cursor:
            cursor.execute(query)
            species_total_count = cursor.fetchall()
            species_total_count = species_total_count[0][0]
        
        others = {'name': '其他物種', 'count': 0, 'y': 0}
        # 取前8名，剩下的統一成其他
        if species_total_count:
            species_last_updated = timezone.now() + timedelta(hours=8)
            species_last_updated = datetime.datetime.strftime(species_last_updated,'%Y-%m-%d') 
            pre_q = Image.objects.filter(project_id=pk)
            if start_date:
                pre_q = pre_q.filter(datetime__gte=start_date)
            if end_date:
                pre_q = pre_q.filter(datetime__lt=end_date)

            query = pre_q.values('species').annotate(total=Count('species')).order_by('-total')
            c = 0
            for i in query:
                if i['species'] == '':
                    s_name = '未填寫'
                else:
                    s_name = i['species']
                    species_count += 1
                c += 1
                if c < 9:
                    pie_data += [{'name': s_name, 'y': round(i['total']/species_total_count*100, 2), 'count': i['total']}]
                else:
                    other_data += [{'name': s_name, 'y': round(i['total']/species_total_count*100, 2), 'count': i['total']}]
                    others.update({'count': others['count']+i['total']})
            if others['count'] > 0:
                others.update({'y': round(others['count']/species_total_count*100, 2)})
                pie_data += [others]


    response = {'pie_data': pie_data, 'other_data': other_data, 'species_count': species_count, 
                'species_last_updated': species_last_updated, 'deployment_points': new_deployment_points}

    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')



def project_info(request, pk):
    project = Project.objects.get(id=pk)
    # 使用者是否有系統管理者/project_admin/總管理人的權限
    is_authorized = check_if_authorized(request, pk)
    is_project_authorized = False
    
    # 系統管理員
    member_id = request.session.get('id', None)
    system_admin = Contact.objects.filter(id=member_id, is_system_admin=True).exists()
    
    # 團隊成員名單
    pm_list = get_project_member(pk)
    if (member_id in pm_list) or is_authorized:
        is_project_authorized = True
    else:
        is_project_authorized = False
    
    # 是否為公開計畫
    is_project_public = Project.objects.filter(id=pk, is_public=True).exists()
    
    sa = StudyArea.objects.filter(project_id=pk, parent_id__isnull=True)
    sa_list = [str(s.id) for s in sa]
    sa_center = [23.5, 121.2]
    zoom = 6
    if sa:
        sa_point = Deployment.objects.filter(study_area_id__in=sa_list, latitude__isnull = False, longitude__isnull = False).order_by('-latitude').values('latitude', 'longitude','geodetic_datum').first()
        if sa_point:
            if sa_point['geodetic_datum'] == 'WGS84':
                sa_center = [float(sa_point['latitude']),float(sa_point['longitude'])]
            else:
                df = pd.DataFrame({
                            'Lat':[int(sa_point['latitude'])],
                            'Lon':[int(sa_point['longitude'])]})

                geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
                gdf = gpd.GeoDataFrame(df, geometry=geometry)

                gdf = gdf.set_crs(epsg=3826, inplace=True)
                gdf = gdf.to_crs(epsg=4326)
                sa_center = [gdf.geometry.y[0],gdf.geometry.x[0]]

            zoom = 8

    species_count = 0
    species_last_updated = None

    query = f"select sum(count) from taicat_projectspecies where project_id={pk};"
    with connection.cursor() as cursor:
        cursor.execute(query)
        species_total_count = cursor.fetchall()
        species_total_count = species_total_count[0][0]

    pie_data = []
    others = {'name': '其他物種', 'count': 0, 'y': 0}
    other_data = []
    # 取前8名，剩下的統一成其他
    if species_total_count:
        if ProjectSpecies.objects.filter(project_id=pk).exists():
            species_count = ProjectSpecies.objects.filter(project_id=pk).exclude(name='').values('name').distinct().count()
            species_last_updated = ProjectSpecies.objects.filter(project_id=pk).annotate(
                last_updated_8=ExpressionWrapper(
                    F('last_updated') + timedelta(hours=8),
                    output_field=DateTimeField()
                )).latest('last_updated_8').last_updated_8
            c = 0
            for i in ProjectSpecies.objects.filter(project_id=pk).order_by('-count'):
                s_name = '未填寫' if i.name == '' else i.name
                c += 1
                if c < 9:
                    pie_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                else:
                    if is_project_authorized:
                        other_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                        others.update({'count': others['count']+i.count})
                    else:
                        if not re.search("人",s_name):
                            other_data += [{'name': s_name, 'y': round(i.count/species_total_count*100, 2), 'count': i.count}]
                            others.update({'count': others['count']+i.count})
                           
            if others['count'] > 0:
                others.update({'y': round(others['count']/species_total_count*100, 2)})
                pie_data += [others]


    return render(request, 'project/project_info.html', {'pk': pk, 'project': project, 'is_authorized': is_authorized,
                                                        'sa_point': sa_center, 'species_count': species_count, 'sa': sa,
                                                        'species_last_updated': species_last_updated, 'pie_data': pie_data,
                                                        'other_data': other_data, 'sa_list': sa_list, 'zoom':zoom, 'is_project_authorized': is_project_authorized,'is_project_public':is_project_public})


def delete_data(request, pk):
    species_list = []
    if request.method == "POST":
        image_list = request.POST.getlist('image_id[]')
        species_list = delete_image_by_ids(image_list, pk)

    response = {'species': species_list}
    return JsonResponse(response, safe=False)  # or JsonResponse({'data': data})


def edit_image(request, pk):
    if request.method == "POST":
        mode = Project.objects.filter(id=pk).first().mode

        now = timezone.now()
        requests = request.POST
        image_id = requests.get('image_id')
        image_id = image_id.split(',')

        keys = ['species', 'life_stage', 'sex', 'antler', 'animal_id', 'remarks']
        updated_dict = {}
        for k in keys:
            updated_dict.update({k: requests.get(k)})

        project_id = requests.get('project_id')
        if project_id:
            updated_dict.update({'project_id': project_id})
        if requests.get('studyarea_id'):
            updated_dict.update({'studyarea_id': requests.get('studyarea_id')})
        if requests.get('deployment_id'):
            updated_dict.update({'deployment_id': requests.get('deployment_id')})

        obj = Image.objects.filter(id__in=image_id)
        # obj_ori = obj
        c = obj.count()  # 更新的照片數量

        # taicat_geostat -> 忽略
        # 抓原本的回來減掉
        species = requests.get('species')
        query = obj.values('species').annotate(total=Count('species')).order_by('-total')
        for q in query:
            # print(q)
            # taicat_species
            if mode == 'official':
                if sp := Species.objects.filter(name=q['species']).first():
                    if sp.count == q['total']: # 該物種全部都先被減掉
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
        if mode == 'official':
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
        if project_id == pk:
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
        elif project_id and project_id != pk:
            if p_sp := ProjectSpecies.objects.filter(name=species, project_id=project_id).first():
                p_sp.count += c
                p_sp.last_updated = now
                p_sp.save()
            else:
                p_sp = ProjectSpecies(
                    name=species,
                    last_updated=now,
                    count=c,
                    project_id=project_id)
                p_sp.save()

        if project_id and project_id != pk:
            # project_stat
            latest_date = obj.latest('datetime').datetime
            earliest_date = obj.earliest('datetime').datetime
            # 舊的減掉, 時間也要改
            if p_stat := ProjectStat.objects.filter(project_id=pk).first():
                p_stat.num_data -= c
                p_stat.last_updated = now
                if latest_date == p_stat.latest_date or earliest_date == p_stat.earliest_date: # 重新計算
                    query = f"select min(datetime), max(datetime) from taicat_image where project_id={pk};"
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        dates = cursor.fetchall()
                    p_latest_date = dates[0][1]
                    p_earliest_date = dates[0][0]
                    p_stat.latest_date = p_latest_date
                    p_stat.earliest_date = p_earliest_date
                p_stat.save()
            # 新的加上去
            if new_p_stat := ProjectStat.objects.filter(project_id=project_id).first():
                new_p_stat.num_data += c
                new_p_stat.last_updated = now
                if not new_p_stat.latest_date:
                    new_p_stat.latest_date = latest_date
                elif latest_date > new_p_stat.latest_date:
                    new_p_stat.latest_date = latest_date
                if not new_p_stat.earliest_date:
                    new_p_stat.earliest_date = earliest_date
                elif earliest_date < new_p_stat.earliest_date:
                    new_p_stat.earliest_date = earliest_date
                new_p_stat.save()
            # taicat_imagefolder
            folder_list = list(obj.order_by('folder_name').values_list('folder_name', flat=True).distinct())
            folder_list = [f for f in folder_list if f != '']
            for f in folder_list:
                # 新的加上去
                if not ImageFolder.objects.filter(project_id=project_id, folder_name=f).exists():
                    if ori_f := ImageFolder.objects.filter(project_id=pk, folder_name=f).first():
                        new_f = ImageFolder(
                            folder_name = f,
                            last_updated = now,
                            project_id = project_id,
                            folder_last_updated = ori_f.folder_last_updated
                        )
                        new_f.save()
                # 舊的如果都不存在的話拿掉
                if not Image.objects.filter(project_id=pk, folder_name=f).exists():
                    ImageFolder.objects.filter(project_id=pk, folder_name=f).delete()

        if updated_dict:
            updated_dict.update({'last_updated': now})
            obj.update(**updated_dict)

        species = ProjectSpecies.objects.filter(project_id=pk).order_by('count').values('count', 'name')
        with connection.cursor() as cursor:
            query = f"""SELECT folder_name,
                        to_char(folder_last_updated AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS folder_last_updated
                        FROM taicat_imagefolder WHERE project_id = {pk}"""
            cursor.execute(query)
            folder_list = cursor.fetchall()
            columns = list(cursor.description)
            results = []
            for row in folder_list:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col.name] = row[i]
                results.append(row_dict)

        response = {'species': list(species), 'folder_list': results}
        return JsonResponse(response, safe=False)  # or JsonResponse({'data': data})


city_list = ['基隆市', '嘉義市', '台北市', '嘉義縣', '新北市', '台南市',
             '桃園縣', '高雄市', '新竹市', '屏東縣', '新竹縣', '台東縣',
             '苗栗縣', '花蓮縣', '台中市', '宜蘭縣', '彰化縣', '澎湖縣',
             '南投縣', '金門縣', '雲林縣',	'連江縣']

species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']


def sortFunction(value):
    return value["id"]

# 使用者是否有系統管理者/project_admin/總管理人的權限
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


# 是否可以看到計畫資訊/詳細內容(使用者是 系統管理者/團隊成員/總管理人，或公開資料)
def check_if_authorized_project(request, pk):
    is_authorized = False
    member_id = request.session.get('id', None)
    if member_id:
        # check system_admin
        if Contact.objects.filter(id=member_id, is_system_admin=True):
            is_authorized = True
        # check project_member 
        elif ProjectMember.objects.filter(member_id=member_id, project_id=pk).exists():
            is_authorized = True
        else:
            # check organization_admin
            if_organization_admin = Contact.objects.filter(id=member_id, is_organization_admin=True)
            if if_organization_admin:
                organization_id = if_organization_admin.values('organization').first()['organization']
                if Organization.objects.filter(id=organization_id, projects=pk):
                    is_authorized = True
    # 計畫是否已公開
    elif Project.objects.filter(id=pk, is_public=True).exists():
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
        study_area = StudyArea.objects.filter(project_id=pk)
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
                data = dict(request.POST)
                data.pop('action')
                data.pop('csrfmiddlewaretoken')
                for i in data:
                    m = re.search(r'(.*?)_studyareas_id', i)
                    if m:
                        list_id = [str(x['id']) for x in list(ProjectMember.objects.get(member_id=m.group(1), project_id=pk).pmstudyarea.all().values('id'))] 
                        for item in data[i]:
                            if item not in list_id:
                                ProjectMember.objects.get(member_id=m.group(1), project_id=pk).pmstudyarea.add(StudyArea.objects.get(id=item))
                        for item in list_id:
                            if item not in data[i]:
                                ProjectMember.objects.get(member_id=m.group(1), project_id=pk).pmstudyarea.remove(StudyArea.objects.get(id=item))
                    else:
                        # 判斷是否有studyarea，有則移除，沒有照舊
                        tmp = str(i)+'_studyareas_id'
                        if tmp not in data.keys():
                            list_id = [str(x['id']) for x in list(ProjectMember.objects.get(member_id=i, project_id=pk).pmstudyarea.all().values('id'))] 
                            if len(list_id) > 0 :
                                for item in list_id:
                                    ProjectMember.objects.get(member_id=i, project_id=pk).pmstudyarea.remove(StudyArea.objects.get(id=item))
                            
                        ProjectMember.objects.filter(member_id=i, project_id=pk).update(role=data[i][0])
                messages.success(request, '儲存成功')
            # Remove member
            else:
                ProjectMember.objects.filter(member_id=data['memberid'], project_id=pk).delete()
                messages.success(request, '移除成功')

        return render(request, 'project/edit_project_members.html', {'members': members, 'pk': pk,
                                                                     'organization_admin': organization_admin,
                                                                     'study_area': study_area, 
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
            query = """SELECT id, name, longitude, latitude, altitude, county, protectedarea, vegetation,landcover, verbatim_locality, 
                        geodetic_datum, deprecated FROM taicat_deployment 
                        WHERE study_area_id = {} ORDER BY id ASC;"""
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
        counties = res.getlist('counties[]')
        protectedareas = res.getlist('protectedareas[]')
        vegetations = res.getlist('vegetations[]')
        did = res.getlist('did[]')
        deprecated = res.getlist('deprecated[]')
        data = []
        ids = []
        for i in range(len(names)):
            if str(i) in deprecated:
                dep = True
            else:
                dep = False
            if altitudes[i] == "":
                altitudes[i] = None
            if did[i]:
                if Deployment.objects.filter(id=did[i]).exists():
                    Deployment.objects.filter(id=did[i]).update(
                        geodetic_datum=geodetic_datum,
                        name=names[i], 
                        longitude=longitudes[i], 
                        latitude=latitudes[i], 
                        altitude=altitudes[i],
                        county=counties[i], 
                        protectedarea=protectedareas[i], 
                        landcover=landcovers[i], 
                        vegetation=vegetations[i],
                        deprecated=dep)
            else:
                new_did = Deployment.objects.create(project_id=project_id, study_area_id=study_area_id, geodetic_datum=geodetic_datum,
                            name=names[i], longitude=longitudes[i], latitude=latitudes[i], altitude=altitudes[i],
                            county=counties[i],protectedarea=protectedareas[i],
                            landcover=landcovers[i], vegetation=vegetations[i], deprecated=dep)
                ids.append(new_did.id)

                if ProjectStat.objects.filter(project_id=project_id).exists():
                    ProjectStat.objects.filter(project_id=project_id).update(num_deployment=Deployment.objects.filter(project_id=project_id).count())
        
        if ids:
            with connection.cursor() as cursor:
                query = f"""SELECT id, name, longitude, latitude, altitude, county, protectedarea, vegetation, landcover, verbatim_locality, 
                            geodetic_datum, deprecated FROM taicat_deployment 
                            WHERE id in ({str(ids).replace('[','').replace(']','')}) ORDER BY id ASC;"""
                cursor.execute(query.format(study_area_id))
                data = cursor.fetchall()


        return HttpResponse(json.dumps(data, cls=DecimalEncoder), content_type='application/json')


def add_studyarea(request):
    if request.method == "POST":
        project_id = request.POST.get('project_id')
        parent_id = request.POST.get('parent_id', None)
        name = request.POST.get('name')

        s = StudyArea.objects.create(name=name, project_id=project_id, parent_id=parent_id)
        data = {'study_area_id': s.id}

        # projectstat
        if ps := ProjectStat.objects.filter(project_id=project_id).first():
            ps.num_sa = StudyArea.objects.filter(project_id=project_id).count()
            ps.last_updated = timezone.now()
            ps.save()

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
    update = False
    p_stat_list = ProjectStat.objects.all().values_list('project_id', flat=True)
    
    if last_updated := ProjectStat.objects.filter(project_id__in=list(project_info.id)).aggregate(Min('last_updated'))['last_updated__min']:
        if Image.objects.filter(created__gte=last_updated, project_id__in=list(project_info.id)).exists():
            update = True
    else:
        update = True
    if update:
        # update project stat
        ProjectStat.objects.filter(project_id__in=list(project_info.id)).update(last_updated=now)
        if last_updated:
            p_list = Image.objects.filter(created__gte=last_updated, project_id__in=list(project_info.id)).order_by('project_id').distinct('project_id').values_list('project_id', flat=True)
        else:
            p_list = list(project_info.id)
        for i in p_list:
            c = Image.objects.filter(project_id=i).count()
            if last_updated:
                image_objects = Image.objects.filter(project_id=i, created__gte=last_updated)
            else:
                image_objects = Image.objects.filter(project_id=i)
            if image_objects.exists():
                latest_date = image_objects.latest('datetime').datetime
                earliest_date = image_objects.earliest('datetime').datetime
            else:
                latest_date, earliest_date = None, None 
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
    # 如果有完全不在project stat裡,且也沒有資料的
    p_no_stat = [ p for p in list(project_info.id) if p not in p_stat_list ]
    for pn in p_no_stat:
        p = ProjectStat(
                project_id=pn,
                num_sa=StudyArea.objects.filter(project_id=pn).count(),
                num_deployment=Deployment.objects.filter(project_id=pn).count(),
                num_data=0,
                last_updated=now,
                latest_date=None,
                earliest_date=None)
        p.save()
    # update project species
    update = False
    last_updated = ProjectSpecies.objects.filter(project_id__in=list(project_info.id)).aggregate(Min('last_updated'))['last_updated__min']
    if last_updated:
        if Image.objects.filter(last_updated__gte=last_updated, project_id__in=list(project_info.id)).exists():
            update = True
    else:
        update = True 
    if update:
        if last_updated:
            p_list = Image.objects.filter(last_updated__gte=last_updated, project_id__in=list(project_info.id)).order_by('project_id').distinct('project_id').values_list('project_id', flat=True)
        else: # 代表完全沒有資料 
            p_list = list(project_info.id)
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
        if ProjectStat.objects.filter(project_id=i).exists():
            obj = ProjectStat.objects.get(project_id=i)
            sa_c = obj.num_sa
            dep_c = obj.num_deployment
            img_c = obj.num_data
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
        # q = "SELECT taicat_project.id FROM taicat_project \
        #     WHERE taicat_project.mode = 'official' AND (CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval);"
        q = "SELECT taicat_project.id FROM taicat_project \
            WHERE taicat_project.mode = 'official' AND taicat_project.is_public = 't';"
        cursor.execute(q)
        public_project_list = [l[0] for l in cursor.fetchall()]
    if public_project_list:
        public_project, public_species_data = get_project_info(str(public_project_list).replace('[', '(').replace(']', ')'))
    # ---------------我的計畫
    # my project
    my_project = []
    my_species_data = []
    if member_id := request.session.get('id', None):
        if my_project_list := get_my_project_list(member_id,[]):
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
                # q = "SELECT taicat_project.id FROM taicat_project \
                #     WHERE taicat_project.mode = 'official' AND (CURRENT_DATE >= taicat_project.publish_date OR taicat_project.end_date < now() - '5 years' :: interval);"
                q = "SELECT taicat_project.id FROM taicat_project \
                    WHERE taicat_project.mode = 'official' AND taicat_project.is_public = 't';"
                cursor.execute(q)
                public_project_list = [l[0] for l in cursor.fetchall()]
            project_list = ProjectSpecies.objects.filter(name__in=species, project_id__in=public_project_list).order_by('project_id').distinct('project_id')
            project_list = list(project_list.values_list('project_id', flat=True))
        else:
            member_id = request.session.get('id', None)
            if member_id := request.session.get('id', None):
                if my_project_list := get_my_project_list(member_id,[]): 
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
    # 使用者是否有系統管理者/project_admin/總管理人的權限
    is_authorized = check_if_authorized(request, pk)
    is_project_authorized = False
    is_public_project = False    
    member_id = request.session.get('id', None)
    
    # 團隊成員
    member_list = get_project_member(pk)
    if is_authorized or (member_id in member_list):
        is_project_authorized = True
    # 公開
    if Project.objects.filter(id=pk, is_public=True).exists():
        is_public_project = True
    
    with connection.cursor() as cursor:
        query = "SELECT name, funding_agency, code, " \
                "principal_investigator, " \
                "to_char(start_date, 'YYYY-MM-DD'), " \
                "to_char(end_date, 'YYYY-MM-DD') FROM taicat_project WHERE id={}"
        cursor.execute(query.format(pk))
        project_info = cursor.fetchone()
    project_info = list(project_info)
    deployment = Deployment.objects.filter(project_id=pk).order_by('name')
    # folder name takes long time
    # folder_list = Image.objects.filter(project_id=pk).order_by('folder_name').distinct('folder_name')
    now = timezone.now()
    # 是否跟新原始資料的紀錄
    update = False
    last_updated = ProjectStat.objects.filter(project_id=pk).aggregate(Min('last_updated'))['last_updated__min']
    if last_updated:
        if Image.objects.filter(created__gte=last_updated, project_id=pk).exists():
            update = True
    else:
        update = True
    if update:
        # update project stat
        ProjectStat.objects.filter(project_id=pk).update(last_updated=now)
        c = Image.objects.filter(project_id=pk).count()
        if last_updated:
            image_objects = Image.objects.filter(project_id=pk, created__gte=last_updated)
        else:
            image_objects = Image.objects.filter(project_id=pk)
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
    update = False
    last_updated = ProjectSpecies.objects.filter(project_id=pk).aggregate(Min('last_updated'))['last_updated__min']
    if last_updated:
        if Image.objects.filter(last_updated__gte=last_updated, project_id=pk).exists():
            update = True
    else:
        update = True
    if update:
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
    # update = False
    last_updated = ImageFolder.objects.filter(project_id=pk).aggregate(Min('last_updated'))['last_updated__min']
    # has_new = Image.objects.exclude(folder_name='').filter(last_updated__gte=last_updated, project_id=pk)
    if last_updated:
        has_new = Image.objects.exclude(folder_name='').filter(last_updated__gte=last_updated, project_id=pk)
    else:
        has_new = Image.objects.exclude(folder_name='').filter(project_id=pk)
    if has_new.exists():
        ImageFolder.objects.filter(project_id=pk).update(last_updated=now)
        if last_updated:
            query = Image.objects.exclude(folder_name='').filter(last_updated__gte=last_updated, project_id=pk).order_by('folder_name').distinct('folder_name').values('folder_name')
        else:
            query = Image.objects.exclude(folder_name='').filter(project_id=pk).order_by('folder_name').distinct('folder_name').values('folder_name')
        for q in query:
            if last_updated:
                f_last_updated = Image.objects.filter(last_updated__gte=last_updated, project_id=pk, folder_name=q['folder_name']).aggregate(Max('last_updated'))['last_updated__max']
            else:
                f_last_updated = Image.objects.filter(project_id=pk, folder_name=q['folder_name']).aggregate(Max('last_updated'))['last_updated__max']
            if img_f := ImageFolder.objects.filter(folder_name=q['folder_name'], project_id=pk).first():
                img_f.folder_last_updated = f_last_updated
                img_f.last_updated = now
                img_f.save()
            else:
                img_f = ImageFolder(
                    folder_name=q['folder_name'],
                    folder_last_updated=f_last_updated,
                    project_id=pk)
                img_f.save()
    if is_authorized:
        species = ProjectSpecies.objects.filter(project_id=pk).values_list('count', 'name').order_by('count')
    else:
        species = ProjectSpecies.objects.filter(project_id=pk).values_list('count', 'name').order_by('count').exclude(name__iregex=r'人')

    if ProjectStat.objects.filter(project_id=pk).first().latest_date and ProjectStat.objects.filter(project_id=pk).first().earliest_date:
        latest_date = ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d")
        earliest_date = ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")
    else:
        latest_date, earliest_date = None, None

    with connection.cursor() as cursor:
        query = f"""SELECT folder_name,
                        to_char(folder_last_updated AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS folder_last_updated
                        FROM taicat_imagefolder
                        WHERE project_id = {pk} 
                        ORDER BY folder_last_updated desc"""
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
    
    # 系統管理員 / 個別計畫承辦人 / 計畫總管理人 跟 check_if_authorized (系統管理者/project_admin/總管理人的權限)結果一樣
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
    if editable:
        pid_list = get_my_project_list(user_id,[])
        projects = Project.objects.filter(pk__in=pid_list)
        project_list = []
        for p in projects:
            project_list += [{'label': p.name, 'value': p.id}]
    else:
        project_list = []
    tmp_county_list = Deployment.objects.filter(project=pk).values("county").distinct("county").exclude(county__exact='').exclude(county__exact=None)
    tmp=[]
    for i in tmp_county_list:
        tmp.append(i['county'])
    county_list = ParameterCode.objects.filter(type='county',parametername__in= tmp).values("name","type","parametername")
    
    tmp_protectedarea_list = Deployment.objects.filter(project=pk).values("protectedarea").distinct("protectedarea").exclude(protectedarea__exact='').exclude(protectedarea__exact=None)
    tmp_protectedarea = set()
    for i in tmp_protectedarea_list:
        item = i['protectedarea'].split(',')
        for j in item:
            tmp_protectedarea.add(j)
    protectedarea_list = ParameterCode.objects.filter(type='protectedarea',parametername__in= tmp_protectedarea).order_by('parametername').values("name","type","parametername")

    altitude_range = Deployment.objects.filter(project_id=pk,deprecated=False).aggregate(Max("altitude"), Min("altitude"))
    altitude__max = altitude_range['altitude__max'] if altitude_range['altitude__max'] != None else 0
    altitude__min = altitude_range['altitude__min'] if altitude_range['altitude__min'] != None else 0


    return render(request, 'project/project_detail.html',
                  {'project_name_len': len(project_info[0]), 'project_info': project_info, 'species': species, 'pk': pk,
                   'study_area': study_area, 'deployment': deployment, 'folder': folder,
                   'earliest_date': earliest_date, 'latest_date': latest_date,
                   'editable': editable, 'is_authorized': is_authorized,
                   'folder_list': results, 'sa_list': list(sa_list), 'sa_d_list': sa_d_list, 
                   'projects': project_list, 'is_project_authorized': is_project_authorized,'is_public_project':is_public_project,
                   'county_list':county_list,'protectedarea_list':protectedarea_list,
                   'altitude__min':altitude__min,'altitude__max':altitude__max})


def update_edit_autocomplete(request):
    if request.method == 'POST':
        if pk := request.POST.get('pk'):
            sa_d_list = Project.objects.get(pk=pk).get_sa_d_list()
            sa_list = Project.objects.get(pk=pk).get_sa_list()
            return JsonResponse({"sa_d_list": sa_d_list, "sa_list": sa_list}, safe=False)


def data(request):
    # t = time.time()
    requests = request.POST
    pk = requests.get('pk')
    _start = requests.get('start')
    _length = requests.get('length')
    orderby = requests.get('orderby', 'datetime')
    sort = requests.get('sort', 'asc')
    # 系統管理員
    member_id = request.session.get('id', None)
    is_project_authorized = Contact.objects.filter(id=member_id, is_system_admin=True).exists()
    is_authorized = check_if_authorized(request, pk)
    # 團隊成員名單
    member_list = get_project_member(pk)    
    if is_authorized or (member_id in member_list):
        is_authorized = True
        is_project_authorized = True
    
    start_date = requests.get('start_date')
    end_date = requests.get('end_date')
    date_filter = ''
    if ((start_date and start_date != ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")) or (end_date and end_date != ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"))):
        if start_date:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.strptime(ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
        if end_date:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        else:
            end_date = datetime.datetime.strptime(ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"), "%Y-%m-%d") + datetime.timedelta(days=1)
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
    else:
        if not is_project_authorized:
            spe_conditions = "AND i.species NOT IN ('人','人（有槍）','人＋狗','狗＋人','獵人','砍草工人','研究人員','研究人員自己','除草工人')"

    time_filter = ''  # 要先減掉8的時差
    if times := requests.get('times'):
        result = datetime.datetime.strptime(f"1990-01-01 {times}", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=-8)
        time_filter = f"AND datetime::time AT TIME ZONE 'UTC' = time '{result.strftime('%H:%M:%S')}'"

    folder_filter = ''
    if folder_name := requests.get('folder_name'):
        folder_filter = f"AND folder_name = '{folder_name}'"
    
    # Deployment table
    county_filter = ''
    if county_name := requests.get('county_name'):
        county_filter = f" AND county = '{county_name}'"
        
    protectarea_filter = ''
    if protectarea_name := requests.get('protectarea_name'):
        protectarea_filter = f" AND protectedarea like '%{protectarea_name}%'"
        
    start_altitude = requests.get('start_altitude')
    end_altitude = requests.get('end_altitude')
    altitude_filter = ''
    if protectarea_name := requests.get('start_altitude'):
        altitude_filter = f" AND altitude BETWEEN {start_altitude} AND {end_altitude}"
    tmp_deployment_sql = """SELECT * FROM taicat_deployment WHERE project_id = {}{}{}{}"""
    deployment_sql = tmp_deployment_sql.format(pk,county_filter,protectarea_filter,altitude_filter)
    
    with connection.cursor() as cursor:
        if is_project_authorized:
            query = """SELECT i.id, i.studyarea_id, i.deployment_id, i.filename, i.species,
                            i.life_stage, i.sex, i.antler, i.animal_id, i.remarks, i.file_url, i.image_uuid, i.from_mongo,
                            to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, i.memo, i.specific_bucket
                            FROM taicat_image i
                            JOIN ({}) d ON d.id = i.deployment_id
                            WHERE i.project_id = {} {} {} {} {} {}
                            ORDER BY {} {}, i.id ASC
                            LIMIT {} OFFSET {}"""
        else:
            query = """SELECT i.id, i.studyarea_id, i.deployment_id, i.filename, i.species,
                            i.life_stage, i.sex, i.antler, i.animal_id, i.remarks, i.file_url, i.image_uuid, i.from_mongo,
                            to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, i.memo, i.specific_bucket
                            FROM taicat_image i
                            JOIN ({}) d ON d.id = i.deployment_id
                            WHERE i.species not in ('人','人（有槍）','人＋狗','狗＋人','獵人','砍草工人','研究人員','研究人員自己','除草工人') and i.project_id = {} {} {} {} {} {}
                            ORDER BY {} {}, i.id ASC
                            LIMIT {} OFFSET {}"""
        # set limit = 1000 to avoid bad psql query plan
        cursor.execute(query.format(deployment_sql,pk, date_filter, conditions, spe_conditions, time_filter, folder_filter, orderby, sort, 1000, _start))
        image_info = cursor.fetchall()
        # print(query.format(pk, date_filter, conditions, spe_conditions, time_filter, folder_filter, 1000, _start))
    if image_info:

        df = pd.DataFrame(image_info, columns=['image_id', 'studyarea_id', 'deployment_id', 'filename', 'species', 'life_stage', 'sex', 'antler',
                                               'animal_id', 'remarks', 'file_url', 'image_uuid', 'from_mongo', 'datetime', 'memo', 'specific_bucket'])[:int(_length)]
        # print(df)
        # print('b', time.time()-t)
        sa_names = pd.DataFrame(StudyArea.objects.filter(id__in=df.studyarea_id.unique()).values('id', 'name', 'parent_id')
                                ).rename(columns={'id': 'studyarea_id', 'name': 'saname', 'parent_id': 'saparent'})
        d_names = pd.DataFrame(Deployment.objects.filter(id__in=df.deployment_id.unique()).values('id', 'name')).rename(columns={'id': 'deployment_id', 'name': 'dname'})
        df = df.merge(d_names).merge(sa_names)

        with connection.cursor() as cursor:
            if is_project_authorized:
                query = """SELECT COUNT(*)
                            FROM taicat_image i
                            JOIN ({}) d ON d.id = i.deployment_id
                            WHERE i.project_id = {} {} {} {} {} {}"""
            else:
                query = """SELECT COUNT(*)
                            FROM taicat_image i
                            JOIN ({}) d ON d.id = i.deployment_id
                            WHERE i.species not in ('人','人（有槍）','人＋狗','狗＋人','獵人','砍草工人','研究人員','研究人員自己','除草工人') and i.project_id = {} {} {} {} {} {}"""
            cursor.execute(query.format(deployment_sql, pk, date_filter, conditions, spe_conditions, time_filter, folder_filter))
            count = cursor.fetchone()
        recordsTotal = count[0]

        # print('c-1', time.time()-t)
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
        # print('d', time.time()-t)
        s3_bucket = settings.AWS_S3_BUCKET

        for i in df.index:
            file_url = df.file_url[i]
            # if filename.split('.')[-1].lower() in ['mp4','avi','mov','wmv'] and not df.from_mongo[i]:
            #     extension = filename.split('.')[-1].lower()
            #     file_url = df.image_uuid[i] + '.' + extension
            # else:
            print(df.image_uuid[i], df.filename[i], 'xxx')
            if df.memo[i] == '2022-pt-data':
                file_url = f"{df.image_id[i]}-m.jpg"
            elif not file_url and not df.from_mongo[i]:
                suffix = Path(df.filename[i]).suffix
                if suffix.upper() not in ['.JPG', '.PNG', '.JPEG']:
                    # file_url = f"video/{df.image_uuid[i]}{suffix}"
                    # video 轉檔後一定是 mp4
                    file_url = f"video/{df.image_uuid[i]}.mp4"
                else:
                    file_url = f"{df.image_uuid[i]}-m.jpg"
            extension = file_url.split('.')[-1].lower()
            file_url = file_url[:-len(extension)]+extension
            # print(file_url)
            if df.specific_bucket[i]:
                s3_bucket = df.specific_bucket[i]

            if not df.from_mongo[i]:
                # new data - image
                if extension in ['jpg', '']:
                    df.loc[i, 'file_url'] = """<img class="img lazy mx-auto d-block h-100p" data-src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" />""".format(s3_bucket, file_url)
                # new data - video
                else:
                    # df.loc[i, 'file_url'] = """
                    # <video class="img lazy mx-auto d-block" controls height="100" preload="none">
                    #     <source src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" type="video/webm">
                    #     <source src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" type="video/mp4">
                    #     抱歉，您的瀏覽器不支援內嵌影片。
                    # </video>
                    # """.format(s3_bucket, file_url, s3_bucket, file_url)
                    df.loc[i, 'file_url'] = """
                    <video class="img lazy mx-auto d-block" controls height="100" preload="none">
                        <source src="https://{}.s3.ap-northeast-1.amazonaws.com/{}" type="video/mp4">
                        抱歉，您的瀏覽器不支援內嵌影片。
                    </video>
                    """.format(s3_bucket, file_url, s3_bucket, file_url)
            else:
                # old data - image
                if extension in ['jpg', '']:
                    df.loc[i, 'file_url'] = """<img class="img lazy mx-auto d-block h-100p" data-src="https://d3gg2vsgjlos1e.cloudfront.net/annotation-images/{}" />""".format(
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
        # print('e', time.time()-t)

        df['edit'] = df.image_id.apply(lambda x: f"<input type='checkbox' class='edit-checkbox' name='edit' value='{x}'>")

        cols = ['edit', 'saname', 'dname', 'filename', 'datetime', 'species', 'life_stage',
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
    # check_authorized to read ppl data
    member_id = request.session.get('id', None)
    project_name = list(Project.objects.filter(id=pk).values("name"))[0]['name']
    # 有權限拿人的資料
    is_authorized = check_if_authorized(request, pk)
    member_list = get_project_member(pk)    
    if is_authorized or (member_id in member_list):
        is_authorized = True
    
    user_role = ParameterCode.objects.get(parametername=Contact.objects.get(id=member_id).identity).name
    date_filter = ''
    if ((start_date and start_date != ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d")) or (end_date and end_date != ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"))):
        if start_date:
          start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.strptime(ProjectStat.objects.filter(project_id=pk).first().earliest_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
        if end_date:
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
        else:
            end_date = datetime.datetime.strptime(ProjectStat.objects.filter(project_id=pk).first().latest_date.strftime("%Y-%m-%d"), "%Y-%m-%d") + datetime.timedelta(days=1)
        date_filter = "AND i.datetime BETWEEN '{}' AND '{}'".format(start_date, end_date)

    conditions = ''
    deployment = requests.getlist('d-filter')
    sa = requests.get('sa-filter')
    if sa:
        conditions += f' AND i.studyarea_id = {sa}'
        if deployment:
            if 'all' not in deployment:
                x = [int(i) for i in deployment]
                x = str(x).replace('[', '(').replace(']', ')')
                conditions += f' AND i.deployment_id IN {x}'
        else:
            conditions = ' AND i.deployment_id IS NULL'
    spe_conditions = ''
    species = requests.getlist('species-filter')
    if species:
        if 'all' not in species:
            x = [i for i in species]
            x = str(x).replace('[', '(').replace(']', ')')
            spe_conditions = f" AND i.species IN {x}"
    else:
        if not is_authorized:
            spe_conditions = "AND i.species NOT IN ('人','人（有槍）','人＋狗','狗＋人','獵人','砍草工人','研究人員','研究人員自己','除草工人')"

    time_filter = ''  # 要先減掉8的時差
    if times := requests.get('times'):
        result = datetime.datetime.strptime(f"1990-01-01 {times}", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=-8)
        time_filter = f" AND i.datetime::time AT TIME ZONE 'UTC' = time '{result.strftime('%H:%M:%S')}'"

    folder_filter = ''
    if folder_name := requests.get('folder_name'):
        folder_filter = f"AND i.folder_name = '{folder_name}'"

    # Deployment table
    county_filter = ''
    county_name = ''
    if county_name_code := requests.get('county_name'):
        county_filter = f" AND county = '{county_name_code}'"
        county_name  = ParameterCode.objects.get(parametername=county_name_code).name

    protectarea_filter = ''
    protectarea_name = ''
    if protectarea_name_code := requests.get('protectarea_name'):
        protectarea_filter = f" AND protectedarea like '%{protectarea_name_code}%'"
        protectarea_name  = ParameterCode.objects.get(parametername=protectarea_name_code).name

    start_altitude = requests.get('start_altitude')
    end_altitude = requests.get('end_altitude')
    altitude_filter = ''
    
    if start_altitude:
        altitude_filter = f" AND altitude BETWEEN {start_altitude} AND {end_altitude}"
    tmp_deployment_sql = """SELECT * FROM taicat_deployment WHERE project_id = {}{}{}{}"""
    deployment_sql = tmp_deployment_sql.format(pk,county_filter,protectarea_filter,altitude_filter)
    
    
    n = f'download_{str(ObjectId())}_{datetime.datetime.now().strftime("%Y-%m-%d")}.csv'
    download_dir = os.path.join(settings.MEDIA_ROOT, 'download')
    sql = f"""copy ( SELECT i.project_id AS "計畫ID", p.name AS "計畫名稱", i.image_uuid AS "影像ID", 
                                concat_ws('/', ssa.name, sa.name) AS "樣區/子樣區", 
                                d.name AS "相機位置", i.filename AS "檔名", to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS "拍攝時間",
                                i.species AS "物種", i.life_stage AS "年齡", i.sex AS "性別", i.antler AS "角況", i.animal_id AS "個體ID", i.remarks AS "備註" 
                            FROM taicat_image i
                            JOIN taicat_studyarea sa ON i.studyarea_id = sa.id
                            LEFT JOIN taicat_studyarea ssa ON sa.parent_id = ssa.id
                            JOIN ({deployment_sql}) d ON d.id = i.deployment_id
                            JOIN taicat_project p ON i.project_id = p.id
                            WHERE i.project_id = {pk} {date_filter} {conditions} {spe_conditions} {time_filter} {folder_filter}
                            ORDER BY i.created DESC, i.project_id ASC ) to stdout with delimiter ',' csv header;"""
    with connection.cursor() as cursor:
        with open(os.path.join(download_dir, n), 'w+') as fp:
            cursor.copy_expert(sql, fp)
    download_url = request.scheme+"://" + \
        request.META['HTTP_HOST']+settings.MEDIA_URL + \
        os.path.join('download', n)
    if settings.ENV == 'prod':
        download_url = download_url.replace('http', 'https')
    # download_log
    condiction_log = f'''專案名稱:{project_name}, 日期：{date_filter}。樣區 / 相機位置：{conditions} 。海拔：{start_altitude}~{end_altitude}。物種：{spe_conditions} 。時間：{time_filter}。縣市：{county_name}。保護留區：{protectarea_name}。資料夾：{folder_filter} 。'''
    download_log_sql = DownloadLog(user_role=user_role, condiction=condiction_log,file_link=download_url)#file_link=download_url
    download_log_sql.save()
    email_subject = '[臺灣自動相機資訊系統] 下載資料'
    email_body = render_to_string('project/download.html', {'download_url': download_url, })
    send_mail(email_subject, email_body, settings.CT_SERVICE_EMAIL, [email])
    # return response

def download_project_oversight(request, pk):
    # TODO auth
    project = Project.objects.get(pk=pk)
    # proj_stats = project.get_or_count_stats()
    # start_year = datetime.datetime.fromtimestamp(proj_stats['working__range'][0]).year
    # end_year = datetime.datetime.fromtimestamp(proj_stats['working__range'][1]).year
    year = request.GET.get('year')
    year_int = int(year)
    stats = project.count_deployment_journal([year_int])

    wb = Workbook()
    ws1 = wb.active
    with NamedTemporaryFile() as tmp:
        for index, (year, data) in enumerate(stats.items()):
            # each year
            headers = ['樣區', '相機位置']
            for x in range(1, 13):
                headers += [f'{x}月(%)', f'{x}月相機運作天數', f'{x}月天數']
            headers += ['平均', '缺失原因']

            if index == 0:
                ws1.append(headers)
                ws1.title = str(year)
            else:
                sheet = wb.create_sheet(year)
                sheet.append(headers)

            values = []
            for sa in data:
                for d in sa['items']:
                    values = [sa['name'], d['name']]
                    for x in d['items']:
                        detail = json.loads(x[1])
                        values +=[x[0], detail[3], detail[4]]

                    values += [d['ratio_year']]
                    values += ['{}: {}'.format(
                        x['label'],
                        x.get('caused', '')
                    ) for x in d['gaps']]
                    if index == 0:
                        ws1.append(values)
                    else:
                        sheet.append(values)

        wb.save(tmp.name)

        tmp.seek(0)
        stream = tmp.read()
        #filename = quote(f'{project.name}_管考_{start_year}-{end_year}.xlsx')
        filename = quote(f'{project.name}_管考_{year}.xlsx')

        #return StreamingHttpResponse(
        #    stream,
        #    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        #    content_type="application/vnd.ms-excel",
            #content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        #)
        response = HttpResponse(content=stream, content_type='application/ms-excel', )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def project_oversight(request, pk):
    '''
    相機有運作天數 / 當月天數
    '''

    is_authorized = check_if_authorized(request, pk)
    public_ids = Project.published_objects.values_list('id', flat=True).all()
    pk = int(pk)
    if (pk in list(public_ids)) or is_authorized:
        project = Project.objects.get(pk=pk)
    else:
        return HttpResponse('no auth')

    if request.method == 'GET':
        year = request.GET.get('year')
        studyarea = request.GET.get('studyarea')

    elif request.method == 'POST':
        year = request.POST.get('year', 0)
        studyarea = request.POST.get('studyarea')

    mn = DeploymentJournal.objects.filter(project_id=project.id).aggregate(Max('working_end'), Min('working_start'))
    year_list = []
    if mn['working_end__max'] and mn['working_start__min']:
        year_list = list(range(mn['working_start__min'].year, mn['working_end__max'].year+1))

    data = {}
    if year or studyarea:
        # deps = project.get_deployment_list(as_object=True)
        if year and studyarea:
            data = project.count_deployment_journal(year_list=[int(year)], studyarea_ids=[int(studyarea)])
        elif year and not studyarea:
            data = project.count_deployment_journal(year_list=[int(year)])
        elif not year and studyarea:
            data = project.count_deployment_journal(year_list=year_list, studyarea_ids=[int(studyarea)])
        #for sa in data[year]:
        #    for d in sa['items']:
        # print (sa['name'], d['id'], d['name'])
        #        dep_obj = Deployment.objects.get(pk=d['id'])
        #        d['gaps'] = dep_obj.find_deployment_journal_gaps(year_int)
        return render(request, 'project/project_oversight.html', {
            'project': project,
            'gap_caused_choices': DeploymentJournal.GAP_CHOICES,
            'month_label_list': [f'{x}月'for x in range(1, 13)],
            'result': data, #data[year] if year else [],
            'year_list': year_list,
        })
    #else:

    print(year, studyarea, 'xxxxxxxxxxxxx')
    return render(request, 'project/project_oversight.html', {
        'project': project,
        'year_list': year_list
    })


@csrf_exempt
def api_create_or_list_deployment_journals(request):
    if request.method == 'POST':
        ret = {
            'message': ''
        }
        data = json.loads(request.body)
        # print(data)
        if deployment := Deployment.objects.get(pk=data['deploymentId']):
            gap_caused = ''
            if text := data.get('text'):
                gap_caused = text
            elif choice := data.get('choice'):
                gap_caused = choice

            dj= DeploymentJournal(
                project_id=deployment.project_id,
                deployment_id=deployment.id,
                studyarea_id=deployment.study_area_id,
                working_start=make_aware(datetime.datetime.fromtimestamp(int(data['range'][0]))),
                working_end=make_aware(datetime.datetime.fromtimestamp(int(data['range'][1]))),
                gap_caused=gap_caused,
                is_effective=False,
                is_gap=True)
            dj.save()
        ret = {
            'message': f'created {dj.id}'
        }
        return JsonResponse(ret)

    if request.method == 'GET':
        return HtmlResponse('list deployment journals')


@csrf_exempt
def api_update_deployment_journals(request, pk):
    if request.method == 'PUT':
        # update
        ret = {
            'message': ''
        }
        if dj := DeploymentJournal.objects.get(pk=pk):
            data = json.loads(request.body)
            #print(data)
            is_changed = False
            if text := data.get('text'):
                dj.gap_caused = text
                is_changed = True
            elif choice := data.get('choice'):
                dj.gap_caused = choice
                is_changed = True
            else:
                dj.gap_caused = ''
                is_changed = True

            if is_changed:
                dj.last_updated = datetime.datetime.now()
                dj.save()
                ret['message'] = 'updated'
                # try:
                #     stats = dj.project.get_or_count_stats()
                #     gap = stats['years'][str(data['year'])][int(data['saIndex'])]['items'][int(data['dIndex'])]['gaps'][int(data['gapIndex'])]
                #     gap['caused'] = dj.gap_caused
                #     dj.project.write_stats(stats)
                #     ret['message'] = 'updated database, updated ucache'
                # except Exception as e:
                #     ret['message'] = 'updated database, update cache error: {}'.format(e)

        return JsonResponse(ret)


def get_gap_choice(request):
    gc = DeploymentJournal.GAP_CHOICES
    return HttpResponse(json.dumps(gc), content_type='application/json')

def get_parameter_name(request):
    if request.method == "GET":
        pn_type = request.GET.get('type')
        if ParameterCode.objects.filter(type=pn_type).exists():
            parameter_name =ParameterCode.objects.filter(type=pn_type).values("name","pmajor","type","parametername")
        else:
            parameter_name = ''
            
            
        code = [{
            'name':x['name'],
            'pmajor': x['pmajor'],
            'type':x['type'],
            'parametername': x['parametername']
        } for x in parameter_name]
        
    return JsonResponse(code, safe=False)

def check_login(request):
    # check_member_authorized
    response = {}
    response['messages'] = False
    member_id = request.session.get('id', None)
    mem_obj = None
    response['redirect'] = True
    if member_id:
        response['redirect'] = False
        mem_obj = Contact.objects.filter(id=member_id).values_list('name','email','identity').first()
        # 資料未填寫完成
        if None in mem_obj or '' in mem_obj :
            response['redirect'] = True
            response['messages'] = '使用者名稱/電子郵件/身份狀態 填寫未完成'
    else:
        # 訪客
        response['redirect'] = False
        response['messages'] = '尚未登入'
    return HttpResponse(json.dumps(response), content_type='application/json')

@require_GET
def robots_txt(request):

    if settings.ENV =='prod':
        lines = [
            "User-Agent: *",
            "Disallow: /admin/",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")

    else:
        lines = [
            "User-Agent: *",
            "Disallow: /",
        ]

        return HttpResponse("\n".join(lines), content_type="text/plain")
