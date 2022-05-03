from taicat.models import *
from django.db import connection
from django.utils import timezone
from django.db.models import Count
import pandas as pd

# ---------- HOMEPAGE STAT ---------- #
now = timezone.now()
print('start HOMEPAGE STAT', now)

with connection.cursor() as cursor:
    query = """SELECT EXTRACT (year FROM datetime) as year, count(distinct(image_uuid)) as count
    FROM taicat_image
    GROUP BY year"""
    cursor.execute(query)
    data_growth_image = cursor.fetchall()
    data_growth_image = pd.DataFrame(data_growth_image, columns=['year', 'num_image']).sort_values('year')
    year_min, year_max = int(data_growth_image.year.min()), int(data_growth_image.year.max())
    year_gap = pd.DataFrame([i for i in range(year_min, year_max+1)], columns=['year'])
    data_growth_image = year_gap.merge(data_growth_image, how='left').fillna(0)
    data_growth_image['cumsum'] = data_growth_image.num_image.cumsum()
    data_growth_image = data_growth_image.drop(columns=['num_image'])

# if exists, update; if not, create
for i in data_growth_image.index:
    if hps := HomePageStat.objects.filter(year=data_growth_image.loc[i, 'year'], type='image').first():
        # print('here')
        hps.count = data_growth_image.loc[i, 'cumsum']
        hps.last_updated = now
        hps.save()
    else:
        new = HomePageStat(
            count=data_growth_image.loc[i, 'cumsum'],
            year=data_growth_image.loc[i, 'year'],
            type='image',
            last_updated=now
        )
        new.save()

# ---------- PROJECT ---------- #
now = timezone.now()
print('start PROJECT STAT', now)
with connection.cursor() as cursor:
    q = "SELECT taicat_project.id, taicat_project.name, taicat_project.keyword, \
                    EXTRACT (year from taicat_project.start_date)::int, \
                    taicat_project.funding_agency, COUNT(DISTINCT(taicat_studyarea.name)) AS num_studyarea \
                    FROM taicat_project \
                    LEFT JOIN taicat_studyarea ON taicat_studyarea.project_id = taicat_project.id \
                    GROUP BY taicat_project.name, taicat_project.funding_agency, taicat_project.start_date, taicat_project.id \
                    ORDER BY taicat_project.start_date DESC;"
    cursor.execute(q)
    project_info = cursor.fetchall()
    project_info = pd.DataFrame(project_info, columns=['id', 'name', 'keyword', 'start_year', 'funding_agency', 'num_studyarea'])

project_info['num_data'] = 0
project_info['num_deployment'] = 0

for i in project_info.id:
    image_c = Image.objects.filter(project_id=i).count()
    dep_c = Deployment.objects.filter(project_id=i).count()
    project_info.loc[project_info['id'] == i, 'num_data'] = image_c
    project_info.loc[project_info['id'] == i, 'num_deployment'] = dep_c

project_info = project_info[['id', 'name', 'keyword', 'start_year', 'funding_agency', 'num_studyarea', 'num_deployment', 'num_data']]

for i in project_info.index:
    latest_date = None
    earliest_date = None
    image_objects = Image.objects.filter(project_id=project_info.loc[i, 'id'])
    if image_objects.exists():
        query = f"select min(datetime), max(datetime) from taicat_image where project_id={project_info.loc[i, 'id']};"
        with connection.cursor() as cursor:
            cursor.execute(query)
            dates = cursor.fetchall()
        latest_date = dates[0][1]
        earliest_date = dates[0][0]
    if ps := ProjectStat.objects.filter(project_id=project_info.loc[i, 'id']).first():
        ps = ProjectStat.objects.filter(project_id=288).first()
        ps.num_sa = project_info.loc[i, 'num_studyarea']
        ps.num_deployment = project_info.loc[i, 'num_deployment']
        ps.num_data = project_info.loc[i, 'num_data']
        ps.last_updated = now
        ps.latest_date = latest_date
        ps.earliest_date = earliest_date
        ps.save()
    else:
        new = ProjectStat(
            project_id=project_info.loc[i, 'id'],
            num_sa=project_info.loc[i, 'num_studyarea'],
            num_deployment=project_info.loc[i, 'num_deployment'],
            num_data=project_info.loc[i, 'num_data'],
            last_updated=now,
            latest_date=latest_date,
            earliest_date=earliest_date,
        )
        new.save()

# ---------- SPECIES ---------- #
now = timezone.now()
print('start SPECIES STAT', now)
query = Image.objects.all().values('species').annotate(total=Count('species')).order_by('-total')
for i in query:
    if sp := Species.objects.filter(name=i['species']).first():
        sp.count = i['total']
        sp.last_updated = now
        sp.save()
    else:
        sp = Species(name=i['species'], last_updated=now, count=i['total'])
        if i['species'] in Species.DEFAULT_LIST:
            sp.status = 'I'
        sp.save()

# delete count = 0
Species.objects.filter(count=0).delete()

# ---------- PROJECTSPECIES ---------- #
now = timezone.now()
print('start PROJECT SPECIES', now)

for p in Project.objects.all().values('id'):
    query = Image.objects.filter(project_id=p['id']).values('species').annotate(total=Count('species')).order_by('-total')
    for i in query:
        if p_sp := ProjectSpecies.objects.filter(name=i['species'], project_id=p['id']).first():
            p_sp.count = i['total']
            p_sp.last_updated = now
            p_sp.save()
        else:
            p_sp = ProjectSpecies(
                name=i['species'],
                last_updated=now,
                count=i['total'],
                project_id=p['id'])
            p_sp.save()

# delete count = 0
ProjectSpecies.objects.filter(count=0).delete()
