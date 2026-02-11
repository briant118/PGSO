from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("", views.operations_index, name="index"),
    path("coordinator/", views.coordinator, name="coordinator"),
    path("barangay-officials/", views.barangay_officials, name="barangay_officials"),
    path("residents-record/", views.residents_record, name="residents_record"),
    path("voters-registration/", views.voters_registration, name="voters_registration"),
]

