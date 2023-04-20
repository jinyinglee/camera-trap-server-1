import json
import math
import logging
import time
from datetime import datetime
import re
import operator
from functools import reduce

from django.shortcuts import render, redirect
from django.http import (
    JsonResponse,
    FileResponse,
    HttpResponse,
)
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import make_aware
from django.db import connection
from django.conf import settings
from django.db.models import (
    OuterRef,
    Subquery,
    Q,
)

from taicat.models import (
    Image,
    Project,
    Deployment,
    StudyArea,
    Species,
    ParameterCode,
)
from .utils import (
    get_species_list,
    calc,
    calc_output,
    calc_output2,
    calc_from_cache,
    calculated_data,
    get_my_project_list,
)

from .views import (
    check_if_authorized,
    check_if_authorized_create,
)


def index(request):
    context = {
        'env': settings.ENV,
        #'JS_BUNDLE_VERSION': settings.JS_BUNDLE_VERSION
    }
    return render(request, 'search/search_index.html', context)

def api_named_areas(request):
    data = {
        'county': [],
        'protectedarea': [],
    }

    county_list = ParameterCode.objects.filter(type='county').all()
    protectedarea_list = ParameterCode.objects.filter(type='protectedarea').all()
    for i in county_list:
        data['county'].append({
            'id': i.id,
            'parametername': i.parametername,
            'name': i.name,
        })
    for i in protectedarea_list:
        data['protectedarea'].append({
            'id': i.id,
            'parametername': i.parametername,
            'name': i.name,
            'category': i.pmajor,
        })
    return JsonResponse({
        'category': 'named_areas',
        'data': data
    })


def api_get_species(request):
    species_list = [x.to_dict() for x in Species.objects.filter(status='I').all()]
    return JsonResponse({
        'category': 'species',
        'data': species_list,
        'total': len(species_list)
    })

def api_get_projects(request):
    public_projects = []
    my_projects = []

    # code from views.project_overview
    is_authorized_create = check_if_authorized_create(request)
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
        #public_project, public_species_data = get_project_info(str(public_project_list).replace('[', '(').replace(']', ')'))
        for p in Project.objects.filter(id__in=public_project_list).all():
            x = p.to_dict()
            x['group_by'] = '公開計畫'
            public_projects.append(x)

    # ---------------我的計畫
    # my project
    # my_project = []
    # my_species_data = []
    if member_id := request.session.get('id', None):
        if my_project_list := get_my_project_list(member_id,[]):
            # my_project, my_species_data = get_project_info(str(my_project_list).replace('[', '(').replace(']', ')'))
            for p in Project.objects.filter(id__in=my_project_list).all():
                x = p.to_dict()
                x['group_by'] = '我的計畫'
                my_projects.append(x)

    projects = public_projects + my_projects
    return JsonResponse({
        'category': 'projects',
        'data': projects,
        'total': len(projects)
    })

def api_deployments(request):
    query = StudyArea.objects.filter()
    resp = {
        'data': [],
    }
    if project_id := request.GET.get('project_id'):
        proj = Project.objects.get(id=project_id)
        project_deployment_list = proj.get_deployment_list()
        query = query.filter(project_id=project_id)
        resp['data'] = project_deployment_list
    return JsonResponse(resp)

def api_search(request):
    rows = []
    #request.is_ajax() and
    if request.method == 'GET':
        start_time = time.time()
        start = 0
        end = 20
        query_start = datetime(2014, 1, 1)
        query_end = datetime.now()
        query = Image.objects.filter()
        # TODO: 考慮 auth
        if request.GET.get('filter'):
            filter_dict = json.loads(request.GET['filter'])
            #print(filter_dict, flush=True)
            project_ids = []
            if value := filter_dict.get('keyword'):
                rows = Project.objects.values_list('id', flat=True).filter(keyword__icontains=value)
                project_ids = list(rows)
                if len(project_ids) > 0:
                    query = query.filter(project_id__in=project_ids)
                else:
                    query = query.filter(project_id__in=[9999]) # 關鍵字沒有就都不要搜到
            #if values := filter_dict.get('projects'):
            #        project_ids = values

            sp_values = []
            if values := filter_dict.get('species'):
                sp_values += values
            if value := filter_dict.get('speciesText'):
                sp_values += [value]

            if value := filter_dict.get('startDate'):
                dt = make_aware(datetime.strptime(value, '%Y-%m-%d'))
                query_start = dt
                query = query.filter(datetime__gte=dt)
            if value := filter_dict.get('endDate'):
                dt = make_aware(datetime.strptime(value, '%Y-%m-%d'))
                query_end = dt
                query = query.filter(datetime__lte=dt)
            if values := filter_dict.get('deployments'):
                query = query.filter(deployment_id__in=values)
                #if len(project_ids):
                #    query = query.filter(Q(deployment_id__in=values) | Q(project_id__in=project_ids))
                # else:
                #    query = query.filter(deployment_id__in=values)
            elif values := filter_dict.get('studyareas'):
                query = query.filter(studyarea_id__in=values)

            if value := filter_dict.get('altitude'):
                if op := filter_dict.get('altitudeOperator'):
                    val_list = value.split('-')
                    v1 = int(val_list[0])
                    v2 = None
                    if len(val_list) >= 2:
                        v2 = int(val_list[1])
                    if v1:
                        if op == 'eq':
                            query = query.filter(deployment__altitude=v1)
                        elif op == 'gt':
                            query = query.filter(deployment__altitude__gte=v1)
                        elif op == 'lt':
                            query = query.filter(deployment__altitude__lte=v1)
                    if v2 and op == 'range':
                        query = query.filter(deployment__altitude__gte=v1, deployment__altitude__lte=v2)

            if values := filter_dict.get('counties'):
                q_list = []
                for x in values:
                    q_list.append(Q(deployment__county__icontains=x['parametername']))

                query = query.filter(reduce(operator.or_, q_list))

            if values := filter_dict.get('protectedareas'):
                q_list = []
                for x in values:
                    q_list.append(Q(deployment__protectedareas__icontains=x['parametername']))

            if len(sp_values) > 0:
                query = query.filter(species__in=sp_values)

        if request.GET.get('pagination'):
            pagination = json.loads(request.GET['pagination'])
            start = pagination['pageIndex'] * pagination['perPage']
            end = start + pagination['perPage']

        download = request.GET.get('download', '')
        calc_data = request.GET.get('calc', '')
        if calc_data:
            calc_data = json.loads(calc_data)

        if download and calc_data:
            calc_dict = json.loads(request.GET['calc'])
            out_format = calc_dict['fileFormat']
            calc_type = calc_dict['calcType']

            # results = calc(query, calc_data, query_start, query_end)
            results = calculated_data(filter_dict, calc_data)
            # print(results, out_format, calc_type)
            #results = calc_from_cache(filter_dict, calc_dict)
            #content = calc_output2(results, out_format, request.GET.get('filter'), request.GET.get('calc'))
            content = calc_output(results, out_format, request.GET.get('filter'), request.GET.get('calc'))

            response = HttpResponse(content)
            response['Content-Type'] = 'text/plain'
            response['Content-Disposition'] = 'attachment; filename=camera-trap-calculation-{}.{}'.format(
                calc_type,
                'csv' if out_format == 'csv' else 'xlsx')
            #print ('--------------', flush=True)
            return response

        else:
            total = query.values('id').order_by('id').count()
            rows = query.all()[start:end]
            # print(query.query, start, end)
            end_time = time.time() - start_time
            return JsonResponse({
                'data': [x.to_dict() for x in rows],
                'total': total,
                'query': str(query.query) if query.query else '',
                'elapsed': end_time,
            })
