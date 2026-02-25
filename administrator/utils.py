"""Permission helpers for Staff vs Admin roles and unrestrict delete per area."""
from django.conf import settings
from django.contrib.auth.models import Group


ADMIN_GROUP_NAME = 'Admin'
STAFF_GROUP_NAME = 'Staff'


def get_fixed_admin_username():
    """Username of the fixed system admin; cannot be changed or have password/permissions edited from app."""
    return getattr(settings, 'FIXED_ADMIN_USERNAME', 'admin')


def is_fixed_admin_user(user):
    """True if this user is the fixed admin (by username)."""
    if not user:
        return False
    return user.username == get_fixed_admin_username()


def _ensure_groups():
    """Create Staff and Admin groups if they don't exist."""
    Group.objects.get_or_create(name=STAFF_GROUP_NAME)
    Group.objects.get_or_create(name=ADMIN_GROUP_NAME)


def user_is_admin(user):
    """True if user is in Admin group or is superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    _ensure_groups()
    return user.groups.filter(name=ADMIN_GROUP_NAME).exists()


def user_is_staff_role(user):
    """True if user is in Staff group (and not Admin)."""
    if not user or not user.is_authenticated:
        return False
    _ensure_groups()
    return user.groups.filter(name=STAFF_GROUP_NAME).exists()


def user_can_delete_in_operations(user):
    """
    True if user may delete in Operations (Coordinator, Barangay Officials, Residents, etc.).
    Admin can always delete. Staff can only if unrestricted via UserProfile.
    """
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    try:
        return user.userprofile.can_delete_in_operations
    except Exception:
        return False


def user_can_delete_in_reference(user):
    """
    True if user may delete in Reference (Barangay, Positions, etc.).
    Admin can always delete. Staff can only if unrestricted via UserProfile.
    """
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    try:
        return user.userprofile.can_delete_in_reference
    except Exception:
        return False
