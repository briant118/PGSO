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


def _get_profile(user):
    try:
        return user.userprofile
    except Exception:
        return None


# === Reference – per-section, per-action ==========================

def user_can_add_reference_barangay(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    # Main toggles (Reference all / Barangay enable) imply full access
    if profile.can_manage_reference or profile.can_manage_reference_barangay:
        return True
    return profile.can_add_reference_barangay


def user_can_edit_reference_barangay(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_reference or profile.can_manage_reference_barangay:
        return True
    return profile.can_edit_reference_barangay


def user_can_delete_reference_barangay(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    # Area-level delete flag still honoured as a fallback
    if profile.can_delete_in_reference:
        return True
    if profile.can_manage_reference or profile.can_manage_reference_barangay:
        return True
    return profile.can_delete_reference_barangay


def user_can_add_reference_position(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_reference or profile.can_manage_reference_position:
        return True
    return profile.can_add_reference_position


def user_can_edit_reference_position(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_reference or profile.can_manage_reference_position:
        return True
    return profile.can_edit_reference_position


def user_can_delete_reference_position(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_delete_in_reference:
        return True
    if profile.can_manage_reference or profile.can_manage_reference_position:
        return True
    return profile.can_delete_reference_position


# === Operations – per-section, per-action =========================

def user_can_add_operations_coordinator(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_coordinator:
        return True
    return profile.can_add_operations_coordinator


def user_can_edit_operations_coordinator(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_coordinator:
        return True
    return profile.can_edit_operations_coordinator


def user_can_delete_operations_coordinator(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_delete_in_operations:
        return True
    if profile.can_manage_operations or profile.can_manage_operations_coordinator:
        return True
    return profile.can_delete_operations_coordinator


def user_can_add_operations_barangay_official(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_barangay_official:
        return True
    return profile.can_add_operations_barangay_official


def user_can_edit_operations_barangay_official(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_barangay_official:
        return True
    return profile.can_edit_operations_barangay_official


def user_can_delete_operations_barangay_official(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_delete_in_operations:
        return True
    if profile.can_manage_operations or profile.can_manage_operations_barangay_official:
        return True
    return profile.can_delete_operations_barangay_official


def user_can_add_operations_residents_record(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_residents_record:
        return True
    return profile.can_add_operations_residents_record


def user_can_edit_operations_residents_record(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_residents_record:
        return True
    return profile.can_edit_operations_residents_record


def user_can_delete_operations_residents_record(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_delete_in_operations:
        return True
    if profile.can_manage_operations or profile.can_manage_operations_residents_record:
        return True
    return profile.can_delete_operations_residents_record


def user_can_add_operations_voters_registration(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_voters_registration:
        return True
    return profile.can_add_operations_voters_registration


def user_can_edit_operations_voters_registration(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_manage_operations or profile.can_manage_operations_voters_registration:
        return True
    return profile.can_edit_operations_voters_registration


def user_can_delete_operations_voters_registration(user):
    if not user or not user.is_authenticated:
        return False
    if user_is_admin(user):
        return True
    profile = _get_profile(user)
    if not profile:
        return False
    if profile.can_delete_in_operations:
        return True
    if profile.can_manage_operations or profile.can_manage_operations_voters_registration:
        return True
    return profile.can_delete_operations_voters_registration
