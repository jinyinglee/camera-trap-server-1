import json

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

from taicat.models import Image, Project

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
def upload_image(request):
    if request.method == 'POST':
        res = {}
        data = json.loads(request.body)
        for i in data:
            img = Image(annotation=json.loads(i[1]))
            img.save()
            res[i[0]] = img.id

        data = {
            'results': res
        }
    return JsonResponse(data)
