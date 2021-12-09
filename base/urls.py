from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logout, name='logout'),
    path('personal_info', views.personal_info, name='personal_info'),
    # path('api/stat_county', views.stat_county, name='stat_county'),
    path('api/get_growth_data', views.get_growth_data, name='get_growth_data'),
    path('api/get_geo_data', views.get_geo_data, name='get_geo_data'),
    path('api/get_species_data', views.get_species_data, name='get_species_data'),
    path('callback/orcid/auth', views.get_auth_callback, name='get_auth_callback'),
    # path('callback/orcid/authcode', views.get_auth_code, name='get_auth_code')
    path('test/login', views.login_for_test, name='login_for_test'),
    path('permission', views.set_permission, name='set_permission'),
    path('add_org_admin', views.add_org_admin, name='add_org_admin'),
    path('policy', views.policy, name='policy'),
]
