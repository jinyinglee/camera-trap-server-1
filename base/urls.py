from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/stat_county', views.stat_county, name='stat_county'),
    path('api/get_home_data', views.get_home_data, name='get_home_data')
]
