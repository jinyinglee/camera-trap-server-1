from django.contrib import admin

from .models import (
    Project,
    StudyArea,
    Deployment,
    Organization,
    Contact,
    ProjectMember
)

@admin.register(ProjectMember)
class ProjectAdmin(admin.ModelAdmin):
    model = ProjectMember


@admin.register(Organization)
class ProjectAdmin(admin.ModelAdmin):
    model = Organization

    filter_horizontal = ('projects',)

@admin.register(Contact)
class ProjectAdmin(admin.ModelAdmin):
    model = Contact

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project

    #filter_horizontal = ('members',)

@admin.register(StudyArea)
class ProjectAdmin(admin.ModelAdmin):
    model = StudyArea

@admin.register(Deployment)
class ProjectAdmin(admin.ModelAdmin):
    model = Deployment

