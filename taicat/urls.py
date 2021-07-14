from django.urls import path
from . import views

urlpatterns = [
    path('project/overview', views.overview, name='overview'),
    path('project/create', views.create_project, name='create_project'),
    path('project/edit/basic/<pk>/', views.edit_project_basic, name='edit_project_basic'),
    path('project/details/<pk>/', views.project_detail, name='project_detail'),
    path('api/data', views.data, name='data')
]
