import json
from datetime import datetime
import pytz
from bson.objectid import ObjectId

from django.shortcuts import render
from django.http import (
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404
from django.conf import settings

from taicat.models import (
    Image,
    Project,
    Deployment,
    DeploymentJournal,
    Image_info,

)

def index(request):
    project_list = Project.objects.filter(mode='test').all()
    return render(request, 'index.html', {'project_list': project_list})

def project_detail(request, pk):
    dep_id = request.GET.get('deployment', '')

    project = Project.objects.get(pk=pk)
    d = project.get_deployment_list()
    #id_list = []
    #for i in d:
    #    for j in i['deployments']:
    #        id_list.append(j['deployment_id'])

    image_list = []
    if dep_id:
        image_list = Image.objects.filter(deployment_id=dep_id).all()

    return render(request, 'project_detail.html',{
        'project':project,
        'deployment': d,
        'image_list': image_list,
    })

def get_project_list(request):
    projects = Project.objects.all()
    ret = {
        'results': [{
            'project_id': x.id,
            'name': x.name,
        } for x in projects]
    }
    return JsonResponse(ret)

def get_project(request, project_id):
    proj = get_object_or_404(Project, pk=project_id)
    data = {
        'project_id': proj.id,
        'name': proj.name,
        'studyareas': proj.get_deployment_list()
    }
    #return HttpResponse(data, content_type="application/json")
    return JsonResponse(data)

@csrf_exempt
def post_image_annotation(request):
    ret = {}
    if request.method == 'POST':
        data = json.loads(request.body)

        deployment = Deployment.objects.get(pk=data['deployment_id'])
        if deployment:
            res = {}
            # aware datetime object
            utc_tz = pytz.timezone(settings.TIME_ZONE)

            # find if is specific_bucket
            bucket_name = data.get('bucket_name', '')
            specific_bucket = ''
            if bucket_name != settings.AWS_S3_BUCKET:
                specific_bucket = bucket_name

            deployment_journal_id = ''
            # create or update DeploymentJournal
            if data.get('trip_start') and data.get('trip_end') and data.get('folder_name') and data.get('source_id'):
                dj_exist = DeploymentJournal.objects.filter(
                    deployment=deployment,
                    folder_name=data['folder_name'],
                    local_source_id=data['source_id']).first()

                if dj_exist:
                    is_modified = False
                    if data['trip_start'] != dj_exist.working_start:
                        dj_exist.working_start = data['trip_start']
                        is_modified = True
                    if data['trip_end'] != dj_exist.working_end:
                        dj_exist.working_end = data['trip_end']
                        is_modified = True

                    if is_modified:
                        dj_exist.save()
                    deployment_journal_id = dj_exist.id

                else:
                    dj_new = DeploymentJournal(
                        deployment_id=deployment.id,
                        project=deployment.project,
                        studyarea=deployment.study_area,
                        working_start=data['trip_start'],
                        working_end=data['trip_end'],
                        folder_name=data['folder_name'],
                        local_source_id=data['source_id'])

                    dj_new.save()
                    deployment_journal_id = dj_new.id

            for i in data['image_list']:
                img_info_payload = None
                # prevent json load error
                exif_str = i[9].replace('\\u0000', '') if i[9] else '{}'
                exif = json.loads(exif_str)
                anno = json.loads(i[7]) if i[7] else '{}'
                if i[11]:
                    is_new_image = False
                    img = Image.objects.get(pk=i[11])
                    # only update annotation
                    img.annotation = anno
                    img.last_updated = datetime.now()
                else:
                    image_uuid = str(ObjectId())
                    img = Image(
                        deployment_id=deployment.id,
                        filename=i[2],
                        datetime=datetime.fromtimestamp(i[3], utc_tz),
                        image_hash=i[6],
                        annotation=anno,
                        memo=data['key'],
                        image_uuid=image_uuid,
                        has_storage='N',
                    )

                    if deployment_journal_id != '':
                        img.deployment_journal_id = deployment_journal_id
                    if specific_bucket != '':
                        img.specific_bucket = specific_bucket

                    img_info_payload = {
                        'source_data': i,
                        'exif': exif,
                        'image_uuid': image_uuid
                    }
                    if pid := deployment.project_id:
                        img.project_id = pid
                    if said := deployment.study_area_id:
                        img.studyarea_id = said

                img.save()
                res[i[0]] = [img.id, img.image_uuid]

                if img_info_payload != None:
                    # seperate image_info
                    img_info = Image_info(
                        image_uuid=img_info_payload['image_uuid'],
                        source_data=img_info_payload['source_data'],
                        exif=img_info_payload['exif'],
                    )
                    img_info.save()

            ret['saved_image_ids'] = res
        else:
            ret['error'] = 'ct-server: no deployment key'

    return JsonResponse(ret)

@csrf_exempt
def update_image(request):
    res = {}
    if request.method == 'POST':
        data = json.loads(request.body)
        if pk := data['pk']:
            image = Image.objects.get(pk=pk)
            if image:
                # limited update field
                if has_storage := data.get('has_storage', ''):
                    image.has_storage = has_storage
                image.save()
        res = {
            'text': 'update-image'
        }
    return JsonResponse(res)

