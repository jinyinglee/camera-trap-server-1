from django.shortcuts import render, HttpResponse
from .models import *
from django.db import connection  # for executing raw SQL
import re
import json
import math


def data(request):
    pk = request.GET.get('pk')
    _start = request.GET.get('start')
    _length = request.GET.get('length')
    species = request.GET.get('species')
    deployment = request.GET.get('deployment')
    sa = request.GET.get('sa')

    with connection.cursor() as cursor:
        query = """with base_request as ( \
                 SELECT 
                        sa.name AS saname, d.name AS dname, i.filename, to_char(i.datetime AT TIME ZONE 'Asia/Taipei', 'YYYY-MM-DD HH24:MI:SS') AS datetime, \
                        i.annotation -> 'species' AS species, i.annotation -> 'lifestage' AS lifestage , i.id FROM taicat_deployment d \
                        JOIN taicat_deployment_study_areas dsa ON dsa.deployment_id = d.id \
                        JOIN taicat_studyarea sa ON sa.id = dsa.studyarea_id \
                        JOIN taicat_image i ON i.deployment_id = d.id \
                        WHERE d.project_id= {} \
                        ORDER BY i.created, i.filename)\
                select row_to_json(t) from ( \
                    select 1 as draw, \
                    ( select array_to_json(array_agg(row_to_json(u)))\
                        from (select * from base_request) u\
                    ) as data) t;"""   
        cursor.execute(query.format(pk))
        image_info = cursor.fetchall()
        image_info = image_info[0][0]
        data = image_info['data']
        if species != "":
            data = [i for i in data if i['species'] == species]
        if sa != "":
            data = [i for i in data if i['saname'] == sa]
        if deployment != "":
            data = [i for i in data if i['dname'] == deployment]

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
        'page': page,  # [opcional]
        'per_page': per_page,  # [opcional]
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
    }

    return HttpResponse(json.dumps(response), content_type='application/json')
    

def overview(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT taicat_project.id, taicat_project.name, \
                        EXTRACT (year from taicat_project.start_date)::int, \
                        taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea, \
                        COUNT(DISTINCT(taicat_deployment.name)) AS num_deployment, \
                        COUNT(taicat_image.id) AS num_image \
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

    studyarea = StudyArea.objects.filter(project_id=pk).values('name').exclude(name=[None, '']).distinct() 
    deployment = Deployment.objects.filter(project_id=pk).values('name','id').exclude(name=[None, '']).distinct() 

    deployment_list = [i['id'] for i in deployment]
    species = Image.objects.filter(deployment_id__in=deployment_list).values('annotation__species').exclude(annotation__species__in=[None, '']).distinct()  # add exclude

    return render(request, 'taicat/project_detail.html',
                {'project_info': project_info, 'species': species, 'pk': pk,
                'studyarea':studyarea, 'deployment':deployment})
