from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logout, name='logout'),
    path('personal_info/update', views.update_personal_info, name='update_personal_info'),
    path('personal_info', views.personal_info, name='personal_info'),
    path('api/stat_county', views.stat_county, name='stat_county'),
    path('api/get_home_data', views.get_home_data, name='get_home_data'),
    path('callback/orcid/auth', views.get_auth_callback, name='get_auth_callback'),
    # path('callback/orcid/authcode', views.get_auth_code, name='get_auth_code')

]
