from taicat.models import *
from django.db import connection  # for executing raw SQL
import pandas as pd
# initial

with connection.cursor() as cursor:
    q = """SELECT project_id, study_area_id, id FROM taicat_deployment 
    """
    cursor.execute(q)
    dep_p = cursor.fetchall()
    dep_p = pd.DataFrame(
        dep_p, columns=['project_id', 'studyarea_id', 'deployment_id'])

# d_list = list(Image.objects.values(
#     'deployment_id').distinct().values_list('deployment_id', flat=True))
# dep_p = dep_p[dep_p.deployment_id.isin(d_list)]
dep_p = dep_p.reset_index()

# for i in range(100):

for i in dep_p.index:
    tmp = dep_p.loc[i]
    print(i)
    if Image.objects.filter(deployment_id=tmp.deployment_id).count() > 0:
        obj = Image.objects.filter(deployment_id=tmp.deployment_id).update(
            project_id=tmp.project_id, studyarea_id=tmp.studyarea_id)
