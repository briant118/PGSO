from django.urls import path
from . import views

app_name = 'mainapplication'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
