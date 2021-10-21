from taicat.models import Image, Deployment


'''
 1. 手動
   -  add Project in admin
   - create studyarea

2. 
'''

PROJECT_ID = 328
STUDY_AREA_ID = 1932
DEPLOYMENT_MAP = {'DS04A': 13769, 'DS02B': 13770, 'DS01B': 13771, 'DS04B': 13772, 'DS02A': 13773, 'DS01A': 13774, 'DS05': 13775, 'DS04': 13776, 'DS11': 13777}

#  add deployment
'''
dep_map = {}
f = open('./scripts/calc-sample.txt')
for i in f:
    d = i.split('\t')
    if d[2] not in dep_map:
        dep = Deployment(name=d[2], study_area_id=STUDY_AREA_ID)
        dep.save()
        dep_map[d[2]] = dep.id

print(dep_map)
'''
f = open('./scripts/calc-sample.txt')
counter = 0
for i in f:
    if counter > 0:
        d = i.split('\t')
        a = {'species': d[5].strip()}
        #print(type(d[4]))
        obj = Image(filename=d[3], datetime=d[4], annotation=a, deployment_id=DEPLOYMENT_MAP[d[2]], memo='calc-sample', studyarea_id=STUDY_AREA_ID, project_id=PROJECT_ID)
        obj.save()
    counter +=1
