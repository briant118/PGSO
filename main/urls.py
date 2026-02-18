from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('mainapplication.urls')),
    path('reference/', include('reference.urls')),
    path('operations/', include('operations.urls')),
    path('reports/', include('reports.urls')),
    path('administrator/', include('administrator.urls')),
]
