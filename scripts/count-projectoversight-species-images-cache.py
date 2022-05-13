from taicat.models import Project, DeploymentJournal
from django.db.models import (
    Max,
    Min,
)
PROJECT_ID = 287
project = Project.objects.get(pk=PROJECT_ID)
deps = project.get_deployment_list(as_object=True)

mnx = DeploymentJournal.objects.filter(project_id=PROJECT_ID, is_effective=True).aggregate(Max('working_end'), Min('working_start'))
end_year = mnx['working_end__max'].year
start_year = mnx['working_start__min'].year
year_list = list(range(start_year, end_year+1))

for year in year_list:
    for sa in deps:
        for d in sa['deployments']:
            dep_id = d['deployment_id']
            year_species_images = d['object'].get_species_images(year)
