import json

from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.http import urlencode

from taicat.models import (
    Image,
    Project
)
from .utils import (
    get_species_list,
    Calculation
)

def index(request):
    species_list = get_species_list(True)
    project_list = Project.objects.all()

    if request.method == 'GET':
        cal = None
        query_type = request.GET.get('query_type', '')
        if query_type:
            cal = Calculation(dict(request.GET))
            if query_type == 'calculate':
                cal.group_by_deployment()
                result = cal.calculate()
            elif query_type == 'query':
                NUM_PER_PAGE = 20
                page = 1
                if p:= request.GET.get('page', ''):
                    page = p
                objects = cal.query.all()
                paginator = Paginator(objects, NUM_PER_PAGE)
                page_obj = paginator.get_page(page)

        project_deployment_list = None
        if p := request.GET.get('project', ''):
            if proj_obj := Project.objects.get(pk=p):
                project_deployment_list = proj_obj.get_deployment_list()

        return render(request, 'search/search_index.html', {
            'species_list': species_list,
            'project_list': project_list,
            'page_obj': page_obj if query_type == 'query' else None,
            'result': result if query_type == 'calculate' else None,
            'project_deployment_list': project_deployment_list,
            'debug_query': str(cal.query.query) if cal else '',
        })
    elif request.method == 'POST':
        base_url = reverse('search')
        args = {}
        print(request.POST)
        if x := request.POST.get('species', ''):
            args['species'] = x
        if x := request.POST.get('project', ''):
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
            base_url = '{}?{}'.format(base_url, urlencode(args))

        return redirect(base_url)
