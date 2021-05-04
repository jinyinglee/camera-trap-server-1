from django.contrib import admin

from .models import (
    Project,
    StudyArea,
    Deployment,
)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project

@admin.register(StudyArea)
class ProjectAdmin(admin.ModelAdmin):
    model = StudyArea

@admin.register(Deployment)
class ProjectAdmin(admin.ModelAdmin):
    model = Deployment
