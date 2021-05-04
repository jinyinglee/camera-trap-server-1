from django.urls import path

from . import views

urlpatterns = [
    #path('', views.index, name='index'),
    path('projects/', views.get_project_list, name='get-project-list'),
    path('projects/<int:project_id>/', views.get_project, name='get-project'),
    path('image/', views.upload_image, name='upload-image'),
]
