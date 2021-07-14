from django.urls import path
from . import views

urlpatterns = [
    path('project/overview', views.project_overview, name='project_overview'),
    path('project/create', views.create_project, name='create_project'),
    path('project/edit/basic/<pk>/', views.edit_project_basic, name='edit_project_basic'),
    path('project/edit/deployment/<pk>/', views.edit_project_deployment, name='edit_project_deployment'),
    path('project/edit/members/<pk>/', views.edit_project_members, name='edit_project_members'),
    path('project/edit/license/<pk>/', views.edit_project_license, name='edit_project_license'),
    path('project/details/<pk>/', views.project_detail, name='project_detail'),
    path('api/data', views.data, name='data')
]
