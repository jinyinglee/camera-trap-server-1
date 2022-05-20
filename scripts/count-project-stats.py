from taicat.models import Project, DeploymentJournal
from django.db.models import (
    Max,
    Min,
)
PROJECT_ID = 287
project = Project.objects.get(pk=PROJECT_ID)

#project.find_and_create_deployment_journal_gap()

project.get_or_count_stats(force=True)
