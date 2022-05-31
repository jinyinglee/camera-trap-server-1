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
    Calculation,
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

def index_depricated(request):
    #species_list = get_species_list()
    #species_list = species_list['all']
    species_list = [[sp.name, sp.count] for sp in Species.objects.filter(status='I').all()]

    # get_project_list
    public_project_list = Project.published_objects.all()
    public_project_ids = [x.id for x in public_project_list]
    private_project_ids = Project.objects.exclude(id__in=public_project_ids).all()
    my_project_list = [p for p in private_project_ids if check_if_authorized(request, p.id)]
    #project_list = my_project_list + list(public_project_list)
    project_list = {
        'public': public_project_list,
        'my': my_project_list
    }
    available_project_ids = [x.id for x in public_project_list] + [x.id for x in my_project_list]

    #print(request.GET)
    if request.method == 'GET':
        cal = None
        start_time = time.time()
        query_type = request.GET.get('query_type', '')
        page_obj = {
            'count': 0,
            'items': [],
            'number': 1,
            'num_pages': 0,
            'has_previous': True,
            'has_next': True,
            'next_page_number': 0,
            'previous_page_number': 0,
        }
        calc_query = None
        if query_type:
            calc = Calculation(dict(request.GET), available_project_ids)
            calc_query = calc.query

            if query_type == 'calculate':
                result = calc.calculate()
            elif query_type == 'query':
                NUM_PER_PAGE = 20
                page = 1
                if p:= request.GET.get('page', ''):
                    page = int(p)

                page_obj['number'] = page

                items = []
                # check filter params
                qs = dict(request.GET)
                for i in ['count', 'query_type']:
                    if i in qs:
                        del qs[i]
                if not qs.keys():
                    # HACK 沒給條件 query 會超慢!
                    with connection.cursor() as cursor:
                        q = 'SELECT id FROM taicat_image ORDER BY datetime DESC LIMIT {}'.format(NUM_PER_PAGE);
                        cursor.execute(q)
                        res = cursor.fetchall()
                        default_ids = [x[0] for x in res]
                    calc_query = calc_query.filter(id__in=default_ids)
                else:
                    calc_query = calc_query.order_by('-datetime')

                page_obj['items'] = calc_query.all()[(page-1)*NUM_PER_PAGE:page*NUM_PER_PAGE]
                #print(cal_query.query)

                #newest = cal.query.filter(post=OuterRef('pk')).order_by('-created_at')
                #print(objects)
                #subquery = str(cal.query.values('id').query)
                #>>> Post.objects.annotate(newest_commenter_email=Subquery(newest.values('email')[:1]))
                count = request.GET.get('count', None)
                if int(count) > 0:
                    page_obj['count'] = int(count)
                else:
                    page_obj['count'] = calc_query.values('id').count() # TO IMPRAVO PERFORMANCE
                    logging.debug('counting', page_obj['count'])
                    to_count = '&count={}'.format(page_obj['count'])
                #request.GET.update({
                #    'count': page_obj['count']
                #})
                page_obj['num_pages'] = math.ceil(page_obj['count'] / NUM_PER_PAGE)
                if page_obj['count'] > page * NUM_PER_PAGE:
                    page_obj['has_next'] = True
                    page_obj['next_page_number'] = page + 1
                    if page > 1:
                        page_obj['has_previous'] = True
                else:
                    page_obj['has_next'] = False

                if page_obj['number'] == 1:
                    page_obj['has_previous'] = False
                page_obj['previous_page_number'] = page - 1 if page > 1 else 1
                #logging.debug(page_obj)

                #print (objects, cal.query.count())
                #paginator = Paginator(objects, NUM_PER_PAGE)
                #page_obj = paginator.get_page(page)

        elapsed_time = time.time() - start_time

        project_deployment_list = None
        if proj_list := request.GET.getlist('project'):
            if len(proj_list) == 1 and proj_list[0] != '':
                if proj_obj := Project.objects.get(pk=proj_list[0]):
                    project_deployment_list = proj_obj.get_deployment_list()

        page_append = request.GET.urlencode()

        ## replace count & delete page
        if page_obj['count'] > 0:
            m = re.match(r'count=(-1|[0-9]+)', page_append)
            if m:
                page_append = page_append.replace(m.group(0), 'count={}'.format(page_obj['count']))
        match_list = [x.group() for x in re.finditer(r'&page=[0-9]*|page=[0-9]*', page_append)]
        for x in match_list:
            page_append = page_append.replace(x, '')

        return render(request, 'search/search_index.html', {
            'species_list': species_list,
            'project_list': project_list,
            #'page_obj': page_obj if query_type == 'query' else None,
            'page_append': page_append,
            'page_obj': page_obj,
            'result': result if query_type == 'calculate' else None,
            'project_deployment_list': project_deployment_list,
            'debug_query': str(calc_query.query) if calc_query != None else '',
            'elapsed_time': elapsed_time,
        })
    elif request.method == 'POST':
        base_url = reverse('search')
        args = {
            'count': -1
        }

        if x := request.POST.get('species', ''):
            args['species'] = x
        if x := request.POST.get('keyword', ''):
            args['keyword'] = x
        if x := request.POST.getlist('project'):
            if len(x) == 1:
                if x[0] != '':
                    args['project'] = x[0]
            else:
                args['project'] = x
        if x := request.POST.get('studyarea', ''):
            args['studyarea'] = x
        if x := request.POST.get('deployment', ''):
            args['deployment'] = x
        if x := request.POST.get('query_type', ''):
            args['query_type'] = x
        if x := request.POST.get('date_start', ''):
            args['date_start'] = x
        if x := request.POST.get('date_end', ''):
            args['date_end'] = x
        if x := request.POST.get('session', ''):
            args['session'] = x
        if x := request.POST.get('interval', ''):
            args['interval'] = x
        if x := request.POST.get('interval2', ''):
            args['interval2'] = x
        #print(args, request.POST)
        if args.get('query_type', '') != 'clear':
            base_url = '{}?{}'.format(base_url, urlencode(args, True))

        return redirect(base_url)


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
        query = Image.objects.filter()
        # TODO: 考慮 auth
        if request.GET.get('filter'):
            filter_dict = json.loads(request.GET['filter'])
            #print(filter_dict, flush=True)

            project_ids = []
            if value := filter_dict.get('keyword'):
                project_ids = Project.objects.values_list('id', flat=True).filter(keyword__icontains=value)
                project_ids = list(project_ids)
            if len(project_ids) > 0:
                query = query.filter(project_id__in=project_ids)
            if values := filter_dict.get('projects'):
                query = query.filter(project_id__in=values)
            if values := filter_dict.get('species'):
                query = query.filter(species__in=values)
            if value := filter_dict.get('startDate'):
                dt = make_aware(datetime.strptime(value, '%Y-%m-%d'))
                query = query.filter(datetime__gte=dt)
            if value := filter_dict.get('endDate'):
                dt = make_aware(datetime.strptime(value, '%Y-%m-%d'))
                query = query.filter(datetime__lte=dt)
            if values := filter_dict.get('deployments'):
                query = query.filter(deployment_id__in=values)
            elif values := filter_dict.get('studyareas'):
                query = query.filter(studyarea_id__in=values)

        if request.GET.get('pagination'):
            pagination = json.loads(request.GET['pagination'])
            start = pagination['page'] * pagination['perPage']
            end = start + pagination['perPage']

        download = request.GET.get('download', '')
        calc_data = request.GET.get('calc', '')
        if calc_data:
            calc_data = json.loads(calc_data)

        if download and calc_data:
            calc_dict = json.loads(request.GET['calc'])
            out_format = calc_dict['fileFormat']
            calc_type = calc_dict['calcType']
            results = calc(query, calc_data)
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
            end_time = time.time() - start_time

            return JsonResponse({
                'data': [x.to_dict() for x in rows],
                'total': total,
                'query': str(query.query) if query.query else '',
                'elapsed': end_time,
            })
