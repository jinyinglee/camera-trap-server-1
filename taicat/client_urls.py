from django.urls import path

from . import client_views

urlpatterns = [
    #path('', views.index, name='index'),
    path('projects/', client_views.get_project_list, name='get-project-list'),
    path('projects/<int:project_id>/', client_views.get_project, name='get-project'),
    path('image/annotation/', client_views.post_image_annotation, name='post-image-annotation'),
    path('image/update/', client_views.update_image, name='update-image'),
]
