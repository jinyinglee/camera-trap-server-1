from django.shortcuts import render, HttpResponse
from .models import *
from django.db import connection  # for executing raw SQL
import re
import json
import math
from datetime import datetime, timedelta


def data(request):
    requests = request.GET
    pk = requests.get('pk')
    start_date = requests.get('start_date')
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = requests.get('end_date')
    end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    _start = requests.get('start')
    _length = requests.get('length')
    species = requests.get('species')
    deployment = requests.get('deployment')
    sa = requests.get('sa')

    with connection.cursor() as cursor:
        query = """with base_request as ( 
                    SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        i.annotation -> 'species' AS species, i.annotation -> 'lifestage' AS lifestage, i.annotation -> 'sex' AS sex, i.annotation -> 'antler' AS antler,
                        i.annotation -> 'remarks' AS remarks, i.annotation -> 'animal_id' AS animal_id,
                        i.id FROM taicat_image i
                        JOIN taicat_deployment d ON d.id = i.deployment_id
                        JOIN taicat_deployment_study_areas dsa ON dsa.deployment_id = d.id 
                        JOIN taicat_studyarea sa ON sa.id = dsa.studyarea_id 
                        WHERE i.annotation = '[]'::jsonb AND d.project_id= {} AND i.datetime BETWEEN '{}' AND '{}' 
                        ORDER BY i.created, i.filename)
                select row_to_json(t) from ( 
                    select 1 as draw, 
                    ( select array_to_json(array_agg(row_to_json(u)))
                        from (select * from base_request) u
                    ) as data) t;"""
        cursor.execute(query.format(pk, start_date, end_date))
        image_info = cursor.fetchall()
        data_0 = image_info[0][0]['data']

    with connection.cursor() as cursor:
        query = """with base_request as ( 
                    SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        x.*,
                        i.id FROM taicat_image i
                        CROSS JOIN LATERAL
                        json_to_recordset(i.annotation::json) x 
                                ( species text, lifestage text
                                , sex text
                                , antler text
                                , remarks text
                                , animal_id text
                                ) 
                        JOIN taicat_deployment d ON d.id = i.deployment_id
                        JOIN taicat_deployment_study_areas dsa ON dsa.deployment_id = d.id 
                        JOIN taicat_studyarea sa ON sa.id = dsa.studyarea_id 
                        WHERE i.id > 426 AND d.project_id= {} AND i.datetime BETWEEN '{}' AND '{}' 
                        ORDER BY i.created, i.filename)
                select row_to_json(t) from ( 
                    select 1 as draw, 
                    ( select array_to_json(array_agg(row_to_json(u)))
                        from (select * from base_request) u
                    ) as data) t;"""
        cursor.execute(query.format(pk, start_date, end_date))
        image_info = cursor.fetchall()
        data_1 = image_info[0][0]['data']

    with connection.cursor() as cursor:
        query = """with base_request as ( 
                    SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, 
                        i.annotation -> 'species' AS species, i.annotation -> 'lifestage' AS lifestage, i.annotation -> 'sex' AS sex, i.annotation -> 'antler' AS antler,
                        i.annotation -> 'remarks' AS remarks, i.annotation -> 'animal_id' AS animal_id,
                        i.id FROM taicat_deployment d 
                        JOIN taicat_deployment_study_areas dsa ON dsa.deployment_id = d.id 
                        JOIN taicat_studyarea sa ON sa.id = dsa.studyarea_id 
                        JOIN taicat_image i ON i.deployment_id = d.id 
                        WHERE i.id < 427 AND d.project_id= {} AND i.datetime BETWEEN '{}' AND '{}' 
                        ORDER BY i.created, i.filename)
                select row_to_json(t) from ( 
                    select 1 as draw, 
                    ( select array_to_json(array_agg(row_to_json(u)))
                        from (select * from base_request) u
                    ) as data) t;"""   
        cursor.execute(query.format(pk, start_date, end_date))
        image_info = cursor.fetchall()
        image_info = image_info[0][0]
        data = image_info['data']

    if data is not None:
        if data_1 is not None:
            data = data + data_1
        if data_0 is not None:
            data = data + data_0
        if species != "":
            data = [i for i in data if i['species'] == species]
        if sa != "":
            data = [i for i in data if i['saname'] == sa]
        if deployment != "":
            data = [i for i in data if i['dname'] == deployment]

        def sortFunction(value):
            return value["id"]
        data = sorted(data, key=sortFunction)

        recordsTotal = len(data)
        recordsFiltered = len(data)

        for i in range(len(data)):
            if data[i]['species'] is not None:
                data[i]['species'] = re.sub(r'^"|"$', '', data[i]['species'])
            else:
                data[i]['species'] = ''
            if data[i]['lifestage'] is not None:
                data[i]['lifestage'] = re.sub(r'^"|"$', '', data[i]['lifestage'])
            else:
                data[i]['lifestage'] = ''
            data[i]['id'] =  """<img class="img lazy" style="height: 200px" data-src="https://camera-trap-21.s3-ap-northeast-1.amazonaws.com/{}.jpg" />""".format(data[i]['id'])

        if _start and _length:
            start = int(_start)
            length = int(_length)
            page = math.ceil(start / length) + 1
            per_page = length
            data = data[start:start + length]

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
    

def overview(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT taicat_project.id, taicat_project.name, \
                        EXTRACT (year from taicat_project.start_date)::int, \
                        taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea, \
                        COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                        COUNT(DISTINCT(taicat_image.id)) AS num_image \
                        FROM taicat_studyarea \
                        RIGHT JOIN taicat_project ON taicat_project.id = taicat_studyarea.project_id \
                        JOIN taicat_deployment ON taicat_deployment.project_id = taicat_project.id \
                        RIGHT JOIN taicat_image ON taicat_image.deployment_id = taicat_deployment.id \
                        GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id '
                       'ORDER BY taicat_project.created DESC;')
        row = cursor.fetchall()

    return render(request, 'taicat/overview.html', {'row': row})


def project_detail(request, pk):
    with connection.cursor() as cursor:
        query = "SELECT name, funding_agency, source_data -> 'code', " \
                "principal_investigator, " \
                "to_char(start_date, 'YYYY-MM-DD'), " \
                "to_char(end_date, 'YYYY-MM-DD') FROM taicat_project WHERE id={}"
        cursor.execute(query.format(pk))
        project_info = cursor.fetchone()
    project_info = list(project_info)

    studyarea = StudyArea.objects.filter(project_id=pk).values('name').exclude(name=[None, '']).distinct().order_by('name') 
    deployment = Deployment.objects.filter(project_id=pk).values('name','id').exclude(name=[None, '']).distinct().order_by('name') 

    deployment_list = [i['id'] for i in deployment]
    species = Image.objects.filter(deployment_id__in=deployment_list).values('annotation__species').exclude(annotation__species__in=[None, '']).distinct().order_by('annotation__species') 

    latest_date = Image.objects.latest('datetime').datetime.strftime("%Y-%m-%d")
    earliest_date = Image.objects.earliest('datetime').datetime.strftime("%Y-%m-%d")


    return render(request, 'taicat/project_detail.html',
                {'project_info': project_info, 'species': species, 'pk': pk,
                'studyarea':studyarea, 'deployment':deployment,
                'earliest_date': earliest_date, 'latest_date':latest_date})
