"""Central activity logging for User Activity page. Call log_activity(request, action, description) from any view."""
from .models import UserActivity

# Action constants for callers that don't import the model
ACTION_CREATE = UserActivity.ACTION_CREATE
ACTION_UPDATE = UserActivity.ACTION_UPDATE
ACTION_DELETE = UserActivity.ACTION_DELETE


def _get_client_ip(request):
    if not request:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _safe_ip(ip_str):
    if not ip_str or not isinstance(ip_str, str):
        return None
    ip_str = ip_str.strip()
    if not ip_str:
        return None
    if ':' in ip_str and len(ip_str) <= 45:
        return ip_str
    parts = ip_str.split('.')
    if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        return ip_str
    return None


def log_activity(request, action, description):
    """
    Record a user action for the User Activity page.
    action: UserActivity.ACTION_CREATE, ACTION_UPDATE, or ACTION_DELETE
    description: short string (max 255 chars), e.g. 'Added barangay "X"'
    """
    if not request:
        return
    user = getattr(request, 'user', None)
    if user and not user.is_authenticated:
        user = None
    ip = _safe_ip(_get_client_ip(request))
    desc = (description or '')[:255]
    try:
        UserActivity.objects.create(
            user=user,
            action=action,
            description=desc,
            ip_address=ip,
        )
    except Exception:
        pass  # don't break the request if logging fails
