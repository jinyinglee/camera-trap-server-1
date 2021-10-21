from django.http import response
from django.shortcuts import render, HttpResponse, redirect
import json
from django.db import connection
from taicat.models import Deployment, Image, Contact, Organization, Project
from django.db.models import Count, Window, F, Sum, Min, Q
from django.db.models.functions import ExtractYear
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.template import loader
import requests
from django.contrib import messages
from decimal import Decimal
import time
import pandas as pd
from .utils import get_cache_growth_data, get_cache_species_data

#init()
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def add_org_admin(request):
    if request.method == 'POST':
        print('hi')
        for i in request.POST:
            print(i)
        redirect(set_permission)


def login_for_test(request):
    next = request.GET.get('next')
    role = request.GET.get('role')
    print(next, role)
    info = Contact.objects.filter(name=role).values('name', 'id').first()
    request.session["is_login"] = True
    request.session["name"] = role
    request.session["orcid"] = ''
    request.session["id"] = info['id']
    request.session["first_login"] = False

    return redirect(next)


def set_permission(request):
    is_authorized = False
    user_id = request.session.get('id', None)
    # check permission
    # if Contact.objects.filter(id=user_id).filter(Q(is_organization_admin=True) | Q(is_system_admin=True)):
    if Contact.objects.filter(id=user_id).filter(is_system_admin=True):
        is_authorized = True

        if request.method == 'POST':
            type = request.POST.get('type')
            if type == 'add_admin':
                user_id = request.POST.get('user', None)
                org_id = request.POST.get('organization', None)
                if user_id and org_id:
                    Contact.objects.filter(id=user_id).update(
                        is_organization_admin=True, organization_id=org_id)
                    messages.success(request, '新增成功')
            elif type == 'remove_admin':
                user_id = request.POST.get('id', None)
                if user_id:
                    Contact.objects.filter(id=user_id).update(
                        is_organization_admin=False)
                    messages.success(request, '移除成功')
            elif type == 'remove_project':
                relation_id = request.POST.get('id', None)
                if relation_id:
                    Organization.projects.through.objects.filter(
                        id=relation_id).delete()
                    messages.success(request, '移除成功')
            else:
                project_id = request.POST.get('project', None)
                org_id = request.POST.get('organization', None)
                try:
                    Organization.objects.get(id=org_id).projects.add(
                        Project.objects.get(id=project_id))
                    messages.success(request, '新增成功')
                except:
                    messages.error(request, '新增失敗')
        member_list = Contact.objects.all().values('name', 'email', 'id')
        org_list = Organization.objects.all()
        project_list = Project.objects.all().values('name', 'id')

        org_project_list = []
        org_project_set = Organization.projects.through.objects.all()
        for i in org_project_set:
            tmp = {'organization_name': i.organization.name, 'relation_id': i.id,
                   'project_name': i.project.name}
            org_project_list.append(tmp)

        org_admin_list = Contact.objects.filter(is_organization_admin=True).values(
            'organization__name', 'id', 'name', 'email')

        return render(request, 'base/permission.html', {'member_list': member_list, 'org_project_list': org_project_list,
                      'is_authorized': is_authorized, 'org_list': org_list, 'project_list': project_list, 'org_admin_list': org_admin_list})
    else:
        messages.error(request, '您的權限不足')
        return render(request, 'base/permission.html', {'is_authorized': is_authorized})


def get_auth_callback(request):
    original_page_url = request.GET.get('next')
    authorization_code = request.GET.get('code')
    data = {'client_id': 'APP-F6POVPAP5L1JOUN1',
            'client_secret': '20acec15-f58b-4653-9695-5e9d2878b673',
            'grant_type': 'authorization_code',
            'code': authorization_code}
    token_url = 'https://orcid.org/oauth/token'

    r = requests.post(token_url, data=data)
    results = r.json()
    orcid = results['orcid']
    name = results['name']

    # check if orcid exists in db
    if Contact.objects.filter(orcid=orcid).exists():
        # if exists, update login status
        info = Contact.objects.filter(orcid=orcid).values('name', 'id').first()
        name = info['name']
        id = info['id']
        request.session["first_login"] = False
    else:
        # if not, create one
        new_user = Contact.objects.create(name=name, orcid=orcid)
        id = new_user.id
        # redirect to set email
        request.session["is_login"] = True
        request.session["name"] = name
        request.session["orcid"] = orcid
        request.session["id"] = id
        request.session["first_login"] = True

        return redirect(personal_info)

    request.session["is_login"] = True
    request.session["name"] = name
    request.session["orcid"] = orcid
    request.session["id"] = id

    return redirect(original_page_url)


def logout(request):
    request.session["is_login"] = False
    request.session["name"] = None
    request.session["orcid"] = None
    request.session["id"] = None
    return redirect('home')


def personal_info(request):
    # login required
    is_login = request.session.get('is_login', False)
    first_login = request.session.get('first_login', False)

    if request.method == 'POST':
        first_login = False
        orcid = request.session.get('orcid')
        name = request.POST.get('name')
        email = request.POST.get('email')
        Contact.objects.filter(orcid=orcid).update(name=name, email=email)
        request.session["name"] = name

    if is_login:
        info = Contact.objects.filter(
            orcid=request.session["orcid"]).values().first()
        return render(request, 'base/personal_info.html', {'info': info, 'first_login': first_login})
    else:
        messages.error(request, '請先登入')
        return render(request, 'base/personal_info.html')


def home(request):
    return render(request, 'base/home.html')


def get_species_data(request):
    response = get_cache_species_data()
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_geo_data(request):
    with connection.cursor() as cursor:
        query = """SELECT d.longitude, d.latitude, p.name FROM taicat_deployment d 
                    JOIN taicat_project p ON p.id = d.project_id 
                    WHERE d.longitude IS NOT NULL;
                    """
        cursor.execute(query)
        deployment_points = cursor.fetchall()
    response = {'deployment_points': deployment_points}
    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')


def get_growth_data(request):
    response = get_cache_growth_data()
    return HttpResponse(json.dumps(response), content_type='application/json')


# ------ deprecated ------ #
def stat_county(request):
    city = request.GET.get('city')
    with connection.cursor() as cursor:
        query = """SELECT COUNT(DISTINCT(d.project_id)), COUNT (i.id) 
        FROM taicat_deployment d
         JOIN taicat_image i ON i.deployment_id = d.id 
         where d.source_data->>'city' = '{}';"""

        cursor.execute(query.format(city))
        response = cursor.fetchone()
    response = {"no_proj": response[0], "no_img": response[1]}
    return HttpResponse(json.dumps(response), content_type='application/json')
