from taicat.models import *
from django.db import connection  # for executing raw SQL

species_map = {'s1': '水鹿', 's2': '山羌', 's3': '獼猴', 's4': '山羊', 's5': '野豬', 's6': '鼬獾', 's7': '白鼻心', 's8': '食蟹獴', 's9': '松鼠',
               's10': '飛鼠', 's11': '黃喉貂', 's12': '黃鼠狼', 's13': '小黃鼠狼', 's14': '麝香貓', 's15': '黑熊', 's16': '石虎', 's17': '穿山甲', 's18': '梅花鹿', 's19': '野兔', 's20': '蝙蝠'}


# initial
with connection.cursor() as cursor:
    q = """SELECT deployment_id, COUNT(id) FROM taicat_image 
    GROUP BY deployment_id
    """
    cursor.execute(q)
    img_by_d = cursor.fetchall()
    img_by_d = pd.DataFrame(
        img_by_d, columns=['deployment_id', 'num_image'])

with connection.cursor() as cursor:
    q = """SELECT project_id, COUNT(id) FROM taicat_deployment 
    GROUP BY project_id
    """
    cursor.execute(q)
    dep_by_p = cursor.fetchall()
    dep_by_p = pd.DataFrame(
        dep_by_p, columns=['project_id', 'num_deployment'])

with connection.cursor() as cursor:
    q = """SELECT project_id, id FROM taicat_deployment 
    """
    cursor.execute(q)
    dep_p = cursor.fetchall()
    dep_p = pd.DataFrame(dep_p, columns=['project_id', 'deployment_id'])

tmp = pd.merge(dep_p, img_by_d, how='right').drop(
    columns=['deployment_id'])
tmp = tmp.groupby(['project_id']).sum().reset_index()
info = pd.merge(
    tmp, dep_by_p, how='left').rename(columns={'project_id': 'id'})

# project list
species_list = ['水鹿', '山羌', '獼猴', '山羊', '野豬', '鼬獾', '白鼻心', '食蟹獴', '松鼠',
                '飛鼠', '黃喉貂', '黃鼠狼', '小黃鼠狼', '麝香貓', '黑熊', '石虎', '穿山甲', '梅花鹿', '野兔', '蝙蝠']
s_all = pd.DataFrame(species_list, columns=['species'])
s_all['num_image'] = 0

for i in info.index:
    print(i, info.loc[i].id)
with connection.cursor() as cursor:
    query = """with b as ( 
                SELECT anno ->> 'species' as s
                FROM taicat_image i 
                LEFT JOIN jsonb_array_elements(i.annotation::jsonb) AS anno ON true    
                WHERE i.annotation::TEXT <> '[]' AND i.deployment_id IN (
                        SELECT d.id FROM taicat_deployment d
                        JOIN taicat_project p ON p.id = d.project_id
                        WHERE d.project_id = {}
                    )
                    )
            select count(*), s from b group by s
            """
    cursor.execute(query.format(info.loc[i].id))
    species_data = cursor.fetchall()
    species_df = pd.DataFrame(species_data, columns=['num_image', 'species'])
    species_data = json.dumps(species_data)
    s_lack = s_all[~s_all.species.isin(species_df.species)]
    species_df = species_df.append(s_lack)

    new_stat = Stat(
        project_id=,
        num_image=,
        num_deployment=,


    )
    new_stat.save()


# num_img

# num_deployment
