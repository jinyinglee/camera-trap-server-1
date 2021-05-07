import json
from datetime import datetime
import pytz

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
    Deployment
)

def index(request):
    project_list = Project.objects.filter(mode='test').all()
    return render(request, 'index.html', {'project_list': project_list})

def project_detail(request, pk):
    project = Project.objects.get(pk=pk)
    return render(request, 'project_detail.html', {'project':project})

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

            for i in data['image_list']:
                anno = json.loads(i[7]) if i[7] else '{}'
                if i[11]:
                    img = Image.objects.get(pk=i[11])
                    # only update annotation
                    img.annotation = anno
                else:
                    img = Image(
                        deployment_id=deployment.id,
                        filename=i[2],
                        datetime=datetime.fromtimestamp(i[3], utc_tz),
                        source_data=i,
                        image_hash=i[6],
                        annotation=anno,
                        memo=data['key']
                    )
                img.save()
                res[i[0]] = img.id

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
                for i in data:
                    if i == 'file_url':
                        image.file_url = data[i]
                image.save()
        res = {
            'text': 'update-image'
        }
    return JsonResponse(res)
