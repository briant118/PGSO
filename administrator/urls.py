from django.urls import path
from . import views

app_name = 'administrator'

urlpatterns = [
    path('', views.administrator_index, name='index'),
    path('system-policy/', views.system_policy, name='system_policy'),
    path('user-accounts/', views.user_accounts, name='user_accounts'),
    path('user-activity/', views.user_activity, name='user_activity'),
]
