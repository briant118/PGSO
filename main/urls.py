from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from . import views as main_views

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('sign-in/', main_views.RoleLoginView.as_view(), name='login'),
    path('sign-out/', main_views.sign_out, name='logout'),
    path('password-reset/', main_views.password_reset_request, name='password_reset'),
    path('password-reset/done/', main_views.password_reset_done, name='password_reset_done'),
    path('admin-forgot-password/', main_views.admin_password_reset_request, name='admin_password_reset'),
    path('admin-forgot-password/verify/', main_views.admin_password_reset_verify, name='admin_password_reset_verify'),
    path('', include('mainapplication.urls')),
    path('reference/', include('reference.urls')),
    path('operations/', include('operations.urls')),
    path('reports/', include('reports.urls')),
    path('administrator/', include('administrator.urls')),
    path('app/', include('app.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
