import json
import math
import logging
import time
from datetime import datetime
import re

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
)
from .utils import (
    get_species_list,
    calc,
    calc_output,
    calc_output2,
    calc_from_cache,
)

from .views import check_if_authorized


def index(request):
    context = {
        'env': settings.ENV,
        #'JS_BUNDLE_VERSION': settings.JS_BUNDLE_VERSION
    }
    return render(request, 'search/search_index.html', context)


def api_get_species(request):
    species_list = [x.to_dict() for x in Species.objects.filter(status='I').all()]
    return JsonResponse({
        'data': species_list,
        'total': len(species_list)
    })

def api_get_projects(request):
    public_project_list = Project.published_objects.all()
    public_project_ids = [x.id for x in public_project_list]
    private_project_list = Project.objects.exclude(id__in=public_project_ids).all()

    public_projects = []
    my_projects = []
    for p in public_project_list:
        x = p.to_dict()
        x['group_by'] = '公開計畫'
        public_projects.append(x)
    for p in private_project_list:
        if check_if_authorized(request, p.id):
            x = p.to_dict()
            x['group_by'] = '我的計畫'
            my_projects.append(x)

    projects = public_projects + my_projects
    return JsonResponse({
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

            results = calc(query, calc_data, query_start, query_end)
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
