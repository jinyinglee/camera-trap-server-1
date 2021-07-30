from django.http import response
from django.shortcuts import render, HttpResponse, redirect
import json
from django.db import connection
from taicat.models import Deployment, Image, Contact
from django.db.models import Count, Window, F, Sum, Min
from django.db.models.functions import ExtractYear
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.template import loader
import requests
from django.contrib import messages

from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def get_auth_callback(request):
    original_page_url = request.GET.get('next')
    authorization_code = request.GET.get('code')
    data = {'client_id': 'APP-F6POVPAP5L1JOUN1',
            'client_secret': '20acec15-f58b-4653-9695-5e9d2878b673',
            'grant_type': 'authorization_code',
            'code': authorization_code}
    token_url = 'https://orcid.org/oauth/token'

    r = requests.post(token_url, data = data)
    results = r.json()
    orcid = results['orcid']
    name = results['name']

    # check if orcid exists in db
    if Contact.objects.filter(orcid=orcid).exists():
    # if exists, update login status
        info = Contact.objects.filter(orcid=orcid).values('name','id').first()
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
    ## login required
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
        info = Contact.objects.filter(orcid=request.session["orcid"]).values().first()
        return render(request, 'base/personal_info.html', {'info': info, 'first_login': first_login})
    else: 
        messages.error(request, '請先登入')
        return render(request, 'base/personal_info.html')


def home(request):
    return render(request, 'base/home.html')


def get_home_data(request):
    with connection.cursor() as cursor:
        query =  """SELECT d.longitude, d.latitude, p.name FROM taicat_deployment d 
                    JOIN taicat_project p ON p.id = d.project_id 
                    WHERE d.longitude IS NOT NULL;
                    """
        cursor.execute(query)
        deployment_points = cursor.fetchall()

    with connection.cursor() as cursor:
        query =  """WITH data AS
                    (SELECT EXTRACT (year FROM datetime) as year, (COUNT(id) OVER (ORDER BY datetime)) count FROM taicat_image)
                    SELECT g.year,
                    (SELECT count
                    FROM data
                    WHERE data.year <= g.year
                    ORDER BY year DESC
                    LIMIT 1)
                    FROM
                    (SELECT (generate_series (MIN(EXTRACT (year FROM datetime))::int, MAX(EXTRACT (year FROM datetime))::int)) as year 
                    FROM taicat_image) g
                    ORDER BY year ASC
        """
        cursor.execute(query)
        data_growth_image = cursor.fetchall()


    with connection.cursor() as cursor:
        query =  """with data_min as (with data as (
            SELECT MIN(EXTRACT (year FROM datetime)) as year, deployment_id FROM taicat_image
            GROUP BY deployment_id) 
            SELECT year,
            count(deployment_id) over (order by year asc rows between unbounded preceding and current row)
            FROM data)
            SELECT g.year,
                (SELECT count
                FROM data_min
                WHERE data_min.year <= g.year
                ORDER BY year DESC
                LIMIT 1)
                FROM
                (SELECT (generate_series (MIN(EXTRACT (year FROM datetime))::int, MAX(EXTRACT (year FROM datetime))::int)) as year 
                FROM taicat_image) g
                ORDER BY year ASC;
        """
        cursor.execute(query)
        data_growth_deployment = cursor.fetchall()

    with connection.cursor() as cursor:
        query =  """with base_request as ( 
                    SELECT 
                        x.*, 
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text
                                ) 
                        WHERE i.id > 426  )
                select count(id), species from base_request
                group by species;
                """
        cursor.execute(query)
        species_data = cursor.fetchall()

    species_list = ['水鹿','山羌','獼猴','山羊','野豬','鼬獾','白鼻心','食蟹獴','松鼠','飛鼠','黃喉貂','黃鼠狼','小黃鼠狼','麝香貓','黑熊','石虎','穿山甲','梅花鹿','野兔','蝙蝠']
    species_data = [ x for x in species_data if x[1] in species_list ]

    response = {'data_growth_image': data_growth_image, 'data_growth_deployment':data_growth_deployment,
     'deployment_points': deployment_points, 'species_data': species_data}

    return HttpResponse(json.dumps(response, cls=DecimalEncoder), content_type='application/json')

def get_deployment_points(request):
    response = {}
    return HttpResponse(json.dumps(response), content_type='application/json')


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