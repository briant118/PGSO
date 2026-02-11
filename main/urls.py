from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mainapplication.urls')),
    path('reference/', include('reference.urls')),
    path('operations/', include('operations.urls')),
    path('reports/', include('reports.urls')),
    path('administrator/', include('administrator.urls')),
]
