from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='index'),
    path('male/', views.list_male, name='list_male'),
    path('male/print/', views.print_male, name='print_male'),
    path('female/', views.list_female, name='list_female'),
    path('female/print/', views.print_female, name='print_female'),
    path('pwd/', views.list_pwd, name='list_pwd'),
    path('pwd/print/', views.print_pwd, name='print_pwd'),
    path('solo-parent/', views.list_solo_parent, name='list_solo_parent'),
    path('solo-parent/print/', views.print_solo_parent, name='print_solo_parent'),
    path('senior-citizen/', views.list_senior_citizen, name='list_senior_citizen'),
    path('senior-citizen/print/', views.print_senior_citizen, name='print_senior_citizen'),
    path('4ps-member/', views.list_4ps_member, name='list_4ps_member'),
    path('4ps-member/print/', views.print_4ps_member, name='print_4ps_member'),
    path('voters/', views.list_voters, name='list_voters'),
    path('voters/print/', views.print_voters, name='print_voters'),
    path('residents-record/', views.list_residents_record, name='list_residents_record'),
    path('residents-record/print/', views.print_residents_record, name='print_residents_record'),
    path('deceased/', views.list_deceased, name='list_deceased'),
    path('deceased/print/', views.print_deceased, name='print_deceased'),
    path('birth-by-year/', views.list_birth_by_year, name='list_birth_by_year'),
    path('birth-by-year/print/', views.print_birth_by_year, name='print_birth_by_year'),
]
