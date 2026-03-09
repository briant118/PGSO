from django.urls import path
from . import views

app_name = 'mainapplication'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/dashboard-birth-death-list/', views.dashboard_birth_death_list, name='dashboard_birth_death_list'),
    path('api/dashboard-activity-chart/', views.dashboard_activity_chart, name='dashboard_activity_chart'),
]
