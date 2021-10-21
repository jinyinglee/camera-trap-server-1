import json
import math
import logging

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
    Project
)
from .utils import (
    get_species_list,
    Calculation
)

def index(request):
    species_list = get_species_list()
    project_list = Project.published_objects.all() #objects.all()
    #print (request.GET)
    if request.method == 'GET':
        cal = None
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
        to_count = ''
        if query_type:
            cal = Calculation(dict(request.GET))
            if query_type == 'calculate':
                cal.group_by_deployment()
                result = cal.calculate()
            elif query_type == 'query':
                NUM_PER_PAGE = 20
                page = 1
                if p:= request.GET.get('page', ''):
                    page = int(p)

                page_obj['number'] = page
                page_obj['items'] = cal.query.all()[(page-1)*NUM_PER_PAGE:page*NUM_PER_PAGE]

                #newest = cal.query.filter(post=OuterRef('pk')).order_by('-created_at')
                #print(objects)
                #subquery = str(cal.query.values('id').query)
                #>>> Post.objects.annotate(newest_commenter_email=Subquery(newest.values('email')[:1]))
                #with connection.cursor() as cursor:
                #    q = f"SELECT COUNT(*) FROM ({subquery}) AS count;"
                #    #print (q, 'uuu')
                #    cursor.execute(q)
                #    foo = cursor.fetchone()
                #    print (foo)
                if c:= request.GET.get('count'):
                    page_obj['count'] = int(c)
                else:
                    page_obj['count'] = cal.query.values('id').count()
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
                        page_obj['previous_page_number'] = page - 1
                else:
                    page_obj['has_next'] = False

                if page_obj['number'] == 1:
                    page_obj['has_previous'] = False

                #logging.debug(page_obj)

                #print (objects, cal.query.count())
                #paginator = Paginator(objects, NUM_PER_PAGE)
                #page_obj = paginator.get_page(page)

        #print (request.GET)
        project_deployment_list = None
        if proj_list := request.GET.getlist('project'):
            if len(proj_list) == 1:
                if proj_obj := Project.objects.get(pk=proj_list[0]):
                    project_deployment_list = proj_obj.get_deployment_list()

        return render(request, 'search/search_index.html', {
            'species_list': species_list,
            'project_list': project_list,
            #'page_obj': page_obj if query_type == 'query' else None,
            'page_obj': page_obj,
            'to_count': to_count,
            'result': result if query_type == 'calculate' else None,
            'project_deployment_list': project_deployment_list,
            'debug_query': str(cal.query.query) if cal else '',
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
