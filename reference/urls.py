from django.urls import path
from . import views

app_name = 'reference'

urlpatterns = [
    path('', views.reference_index, name='index'),
    path('barangay/', views.barangay_list, name='barangay_list'),
    path('positions/', views.position_list, name='position_list'),
]
