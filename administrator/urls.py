from django.urls import path
from . import views

app_name = 'administrator'

urlpatterns = [
    path('', views.administrator_index, name='index'),
    path('system-policy/', views.system_policy, name='system_policy'),
    path('user-accounts/', views.user_accounts, name='user_accounts'),
    path('user-accounts/add/', views.user_add, name='user_add'),
    path('user-accounts/<int:pk>/change-password/', views.user_change_password, name='user_change_password'),
    path('user-accounts/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('user-accounts/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('user-permissions/', views.user_permissions, name='user_permissions'),
    path('user-permissions/<int:pk>/edit/', views.user_permissions_edit, name='user_permissions_edit'),
    path('user-activity/', views.user_activity, name='user_activity'),
]
