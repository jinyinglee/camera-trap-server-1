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
class OrganizationAdmin(admin.ModelAdmin):
    model = Organization

    filter_horizontal = ('projects',)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    model = Contact

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    model = Project

    #filter_horizontal = ('members',)

@admin.register(StudyArea)
class StudyAreaAdmin(admin.ModelAdmin):
    model = StudyArea
    list_display = ('name', 'project')

@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    model = Deployment
    list_display = ('name', 'project', 'study_area')
