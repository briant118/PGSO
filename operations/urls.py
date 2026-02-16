from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("", views.operations_index, name="index"),
    path("coordinator/", views.coordinator, name="coordinator"),
    path("barangay-officials/", views.barangay_officials, name="barangay_officials"),
    path("barangay-official/add/", views.barangay_official_add, name="barangay_official_add"),
    path("barangay-official/get/<int:pk>/", views.barangay_official_get, name="barangay_official_get"),
    path("barangay-official/edit/<int:pk>/", views.barangay_official_edit, name="barangay_official_edit"),
    path("barangay-official/delete/<int:pk>/", views.barangay_official_delete, name="barangay_official_delete"),
    path("residents-record/", views.residents_record, name="residents_record"),
    path("resident/add/", views.resident_add, name="resident_add"),
    path("resident/get/<int:pk>/", views.resident_get, name="resident_get"),
    path("resident/edit/<int:pk>/", views.resident_edit, name="resident_edit"),
    path("resident/delete/<int:pk>/", views.resident_delete, name="resident_delete"),
    path("voters-registration/", views.voters_registration, name="voters_registration"),
]

