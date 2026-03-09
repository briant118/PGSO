"""Context processors for templates."""
from administrator.models import PasswordChangeRequest
from administrator.utils import user_is_admin


def pending_email_requests(request):
    """Add pending_request_count for admin users (unread password change requests)."""
    context = {}
    if request.user.is_authenticated and user_is_admin(request.user):
        context['pending_request_count'] = PasswordChangeRequest.objects.filter(
            status=PasswordChangeRequest.STATUS_PENDING,
            read_at__isnull=True,
        ).count()
    else:
        context['pending_request_count'] = 0
    return context
