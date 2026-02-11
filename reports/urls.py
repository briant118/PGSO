from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='index'),
    path('male/', views.list_male, name='list_male'),
    path('female/', views.list_female, name='list_female'),
    path('pwd/', views.list_pwd, name='list_pwd'),
    path('solo-parent/', views.list_solo_parent, name='list_solo_parent'),
    path('senior-citizen/', views.list_senior_citizen, name='list_senior_citizen'),
    path('4ps-member/', views.list_4ps_member, name='list_4ps_member'),
    path('voters/', views.list_voters, name='list_voters'),
    path('residents-record/', views.list_residents_record, name='list_residents_record'),
]
