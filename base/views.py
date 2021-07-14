from django.http import response
from django.shortcuts import render, HttpResponse
import json
from django.db import connection
from taicat.models import Deployment, Image
from django.db.models import Count, Window, F, Sum, Min
from django.db.models.functions import ExtractYear
from django.contrib.postgres.fields.jsonb import KeyTextTransform


def home(request):
    deployment_points = Deployment.objects.filter(longitude__isnull=False, latitude__isnull=False).only("longitude", "latitude", "project__name")

    with connection.cursor() as cursor:
        query =  """WITH data AS
                    (SELECT EXTRACT (year FROM datetime) as year, (COUNT(id) OVER (ORDER BY datetime))::numeric / 10000 count FROM taicat_image)
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

    # species_data = Image.objects.filter(annotation__species__in=species_list).annotate(name=KeyTextTransform('species', 'annotation')).order_by('name').annotate(c=Count('name')).distinct().order_by('c').values('name','c')

    return render(request, 'base/home.html', {'data_growth_image': data_growth_image, 'data_growth_deployment':data_growth_deployment,
     'deployment_points': deployment_points, 'species_data': species_data})


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