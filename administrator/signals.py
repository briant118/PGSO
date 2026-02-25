from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import UserActivity


def _get_client_ip(request):
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _safe_ip(ip_str):
    """Return ip_str if it looks valid for GenericIPAddressField, else None."""
    if not ip_str or not isinstance(ip_str, str):
        return None
    ip_str = ip_str.strip()
    if not ip_str:
        return None
    # GenericIPAddressField accepts IPv4 and IPv6; allow common cases
    if ':' in ip_str and len(ip_str) <= 45:
        return ip_str
    parts = ip_str.split('.')
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return ip_str
    return None


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = _safe_ip(_get_client_ip(request))
    UserActivity.objects.create(
        user=user,
        action=UserActivity.ACTION_LOGIN,
        description='User logged in successfully',
        ip_address=ip,
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = _safe_ip(_get_client_ip(request))
    UserActivity.objects.create(
        user=user,
        action=UserActivity.ACTION_LOGOUT,
        description='User logged out',
        ip_address=ip,
    )
