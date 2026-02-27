from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.app_info, name='app_info'),
    path('api/residents/search/', views.residents_search_api, name='residents_search'),
    path('api/resident/<int:pk>/', views.resident_api, name='resident_api'),
    path('resident/<int:pk>/', views.resident_profile, name='resident_profile'),
    path('resident/<int:pk>/pdf/', views.resident_profile_pdf, name='resident_profile_pdf'),
]
