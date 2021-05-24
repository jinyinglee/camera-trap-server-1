from django.urls import path
from . import views

urlpatterns = [
    path('project/overview', views.overview, name='overview'),
    path('project/<pk>/', views.project_detail, name='project_detail'),
    path('api/data', views.data, name='data')
]
