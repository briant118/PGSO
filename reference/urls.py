from django.urls import path
from . import views

app_name = 'reference'

urlpatterns = [
    path('', views.reference_index, name='index'),
    path('barangay/', views.barangay_list, name='barangay_list'),
    path('barangay/add/', views.barangay_add, name='barangay_add'),
    path('barangay/edit/<int:pk>/', views.barangay_edit, name='barangay_edit'),
    path('barangay/delete/<int:pk>/', views.barangay_delete, name='barangay_delete'),
    path('barangay/get/<int:pk>/', views.barangay_get, name='barangay_get'),
    path('positions/', views.position_list, name='position_list'),
]
