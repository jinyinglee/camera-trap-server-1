from django.urls import path
from . import (
    views,
    search_view
)

urlpatterns = [
    path('project/overview', views.project_overview, name='project_overview'),
    path('project/create', views.create_project, name='create_project'),
    path('project/edit/basic/<pk>/', views.edit_project_basic, name='edit_project_basic'),
    path('project/edit/deployment/<pk>/', views.edit_project_deployment, name='edit_project_deployment'),
    path('project/edit/members/<pk>/', views.edit_project_members, name='edit_project_members'),
    path('project/edit/license/<pk>/', views.edit_project_license, name='edit_project_license'),
    path('project/details/<pk>/', views.project_detail, name='project_detail'),
    path('project/oversight/<pk>/', views.project_oversight, name='project_oversight'),
    path('project/oversight/<pk>/download/', views.download_project_oversight, name='download_project_oversight'),
    path('search/', search_view.index, name='search'),
    path('api/data', views.data, name='data'),
    path('api/update_datatable', views.update_datatable, name='update_datatable'),
    path('api/deployment/', views.get_deployment, name='deployment'),
    path('api/add_studyarea', views.add_studyarea, name='add_studyarea'),
    path('api/add_deployment', views.add_deployment, name='add_deployment'),
    path('api/edit_image/<pk>', views.edit_image, name='edit_image'),
    path('download/<pk>', views.download_request, name='download'),
    #    path('download/data/<uidb64>/<token>', views.download_data, name='download_data'),
    path('api/species', search_view.api_get_species, name='get_species'),
    path('api/projects', search_view.api_get_projects, name='get_projects'),
    path('api/deployments', search_view.api_deployments, name='get_deployments'),
    path('api/search', search_view.api_search, name='get_search'),
    path('delete/<pk>/', views.delete_data, name='delete_data'),
]
