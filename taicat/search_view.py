import json
import math
import logging
import time
import re

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.http import urlencode
from django.db import connection
from django.db.models import (
    OuterRef,
    Subquery,
)

from taicat.models import (
    Image,
    Project,
    Species,
)
from .utils import (
    get_species_list,
    Calculation
)
from .views import check_if_authorized

def index(request):
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

        if query_type:
            cal = Calculation(dict(request.GET))
            if query_type == 'calculate':
                result = cal.calculate()
            elif query_type == 'query':
                NUM_PER_PAGE = 20
                page = 1
                if p:= request.GET.get('page', ''):
                    page = int(p)

                page_obj['number'] = page

                # check filter params
                qs = dict(request.GET)
                for i in ['count', 'query_type']:
                    if i in qs:
                        del qs[i]

                items = cal.query.order_by('-datetime').all()[(page-1)*NUM_PER_PAGE:page*NUM_PER_PAGE]
                page_obj['items'] = items

                #newest = cal.query.filter(post=OuterRef('pk')).order_by('-created_at')
                #print(objects)
                #subquery = str(cal.query.values('id').query)
                #>>> Post.objects.annotate(newest_commenter_email=Subquery(newest.values('email')[:1]))
                count = request.GET.get('count', None)
                if int(count) > 0:
                    page_obj['count'] = int(count)
                else:
                    page_obj['count'] = cal.query.values('id').count() # TO IMPRAVO PERFORMANCE
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
            'debug_query': str(cal.query.query) if cal else '',
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
        if x := request.POST.get('interval', ''):
            args['interval'] = x
        if x := request.POST.get('interval2', ''):
            args['interval2'] = x
        #print(args, request.POST)
        if args.get('query_type', '') != 'clear':
            base_url = '{}?{}'.format(base_url, urlencode(args, True))

        return redirect(base_url)
