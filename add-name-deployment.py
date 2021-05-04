from taicat.models import Deployment

a = Deployment.objects.all()
for i in a:
    name = i.source_data['name']
    i.name = name
    i.save()
