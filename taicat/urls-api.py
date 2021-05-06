from django.urls import path

from . import views

urlpatterns = [
    #path('', views.index, name='index'),
    path('projects/', views.get_project_list, name='get-project-list'),
    path('projects/<int:project_id>/', views.get_project, name='get-project'),
    path('image/annotation/', views.post_image_annotation, name='post-image-annotation'),
    path('image/update/', views.update_image, name='update-image'),
]
