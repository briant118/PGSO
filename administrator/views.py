from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.views.decorators.http import require_http_methods
from .models import UserProfile, UserActivity
from .utils import ADMIN_GROUP_NAME, STAFF_GROUP_NAME, user_is_admin, is_fixed_admin_user, get_fixed_admin_username
from .activity_log import log_activity

User = get_user_model()


def admin_required(view_func):
    """Decorator: redirect Staff to dashboard; only Admin can access."""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('mainapplication:dashboard')
        if not user_is_admin(request.user):
            messages.error(request, 'You do not have access to Administrator Control.')
            return redirect('mainapplication:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped


def _ensure_groups():
    Group.objects.get_or_create(name=STAFF_GROUP_NAME)
    Group.objects.get_or_create(name=ADMIN_GROUP_NAME)


@admin_required
def administrator_index(request):
    """Administrator control index view"""
    return render(request, 'administrator/administrator_index.html')


@admin_required
def system_policy(request):
    """System policy management"""
    return render(request, 'administrator/system_policy.html')


@admin_required
def user_accounts(request):
    """User accounts management – list all registered users."""
    users = User.objects.all().order_by('-date_joined')
    users_with_roles = [
        {'user': u, 'role': 'Admin' if user_is_admin(u) else 'Staff', 'is_admin': user_is_admin(u)}
        for u in users
    ]
    can_manage = user_is_admin(request.user)
    return render(request, 'administrator/user_accounts.html', {
        'users_with_roles': users_with_roles,
        'can_manage_users': can_manage,
        'fixed_admin_username': get_fixed_admin_username(),
    })


@admin_required
def user_permissions(request):
    """List users with their role and delete permissions; link to edit."""
    users = User.objects.all().order_by('username')
    fixed_username = get_fixed_admin_username()
    rows = []
    for u in users:
        is_admin = user_is_admin(u)
        role = 'Admin' if is_admin else 'Staff'
        try:
            profile = u.userprofile
            can_ops = profile.can_delete_in_operations
            can_ref = profile.can_delete_in_reference
        except Exception:
            can_ops = can_ref = False
        rows.append({
            'user': u,
            'role': role,
            'can_delete_in_operations': can_ops or is_admin,
            'can_delete_in_reference': can_ref or is_admin,
            'is_fixed_admin': u.username == fixed_username,
        })
    return render(request, 'administrator/user_permissions.html', {'rows': rows})


@admin_required
@require_http_methods(['GET', 'POST'])
def user_permissions_edit(request, pk):
    """Set role (Staff/Admin) and unrestrict delete for Operations and Reference."""
    user = get_object_or_404(User, pk=pk)
    if is_fixed_admin_user(user):
        messages.error(request, 'Permissions for the fixed admin account cannot be changed.')
        return redirect('administrator:user_accounts')
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={
        'can_delete_in_operations': False,
        'can_delete_in_reference': False,
    })
    admin_group = None
    staff_group = None
    try:
        from django.contrib.auth.models import Group
        admin_group = Group.objects.filter(name=ADMIN_GROUP_NAME).first()
        staff_group = Group.objects.filter(name=STAFF_GROUP_NAME).first()
    except Exception:
        pass

    if request.method == 'POST':
        role = request.POST.get('role', 'staff').strip().lower()
        can_ops = request.POST.get('can_delete_in_operations') == 'on'
        can_ref = request.POST.get('can_delete_in_reference') == 'on'

        if admin_group and staff_group:
            if role == 'admin':
                user.groups.remove(staff_group)
                user.groups.add(admin_group)
            else:
                user.groups.remove(admin_group)
                user.groups.add(staff_group)

        profile.can_delete_in_operations = can_ops
        profile.can_delete_in_reference = can_ref
        profile.save()
        log_activity(request, UserActivity.ACTION_UPDATE, f'Updated permissions for user "{user.username}".')
        messages.success(request, f'Permissions for {user.username} updated.')
        return redirect('administrator:user_permissions')

    is_admin = user_is_admin(user)
    return render(request, 'administrator/user_permissions_edit.html', {
        'user': user,
        'profile': profile,
        'is_admin': is_admin,
        'admin_group': admin_group,
        'staff_group': staff_group,
    })


@admin_required
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def user_add(request):
    """Admin only: create new user with username, full name, role, password. Saves to database."""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to add users.')
        return redirect('administrator:user_accounts')
    _ensure_groups()
    admin_group = Group.objects.get(name=ADMIN_GROUP_NAME)
    staff_group = Group.objects.get(name=STAFF_GROUP_NAME)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', 'staff').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        email = request.POST.get('email', '').strip()

        errors = []
        if not username:
            errors.append('Username is required.')
        if username.lower() == get_fixed_admin_username().lower():
            errors.append('This username is reserved for the system admin.')
        if User.objects.filter(username__iexact=username).exists():
            errors.append('That username is already taken.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        elif password != password_confirm:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'administrator/user_add.html', {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'email': email,
            })

        # Save user account to database (auth_user + groups + profile)
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email or '',
            is_staff=True,
            is_active=True,
        )
        if role == 'admin':
            user.groups.add(admin_group)
        else:
            user.groups.add(staff_group)
        UserProfile.objects.get_or_create(user=user, defaults={
            'can_delete_in_operations': False,
            'can_delete_in_reference': False,
        })
        log_activity(request, UserActivity.ACTION_CREATE, f'Added user "{username}" (role: {role}).')
        messages.success(request, f'User "{username}" created successfully.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_add.html', {'role': 'staff'})


@admin_required
@require_http_methods(['GET', 'POST'])
def user_change_password(request, pk):
    """Admin only: change another user's password. For fixed admin, email is required (must be set and confirmed)."""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to change passwords.')
        return redirect('administrator:user_accounts')
    target_user = get_object_or_404(User, pk=pk)
    is_fixed = is_fixed_admin_user(target_user)

    if is_fixed and not (target_user.email or '').strip():
        messages.error(request, 'The fixed admin account must have an email set before changing password. Set it in Django Admin.')
        return redirect('administrator:user_accounts')

    if request.method == 'POST':
        if is_fixed:
            confirm_email = request.POST.get('confirm_email', '').strip()
            if confirm_email != (target_user.email or '').strip():
                messages.error(request, 'Email does not match the admin account email.')
                return render(request, 'administrator/user_change_password.html', {
                    'target_user': target_user,
                    'is_fixed_admin': True,
                })
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')

        if not new_password:
            messages.error(request, 'Password is required.')
            return render(request, 'administrator/user_change_password.html', {
                'target_user': target_user,
                'is_fixed_admin': is_fixed,
            })
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'administrator/user_change_password.html', {
                'target_user': target_user,
                'is_fixed_admin': is_fixed,
            })
        if new_password != new_password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'administrator/user_change_password.html', {
                'target_user': target_user,
                'is_fixed_admin': is_fixed,
            })

        target_user.set_password(new_password)
        target_user.save()
        log_activity(request, UserActivity.ACTION_UPDATE, f'Changed password for user "{target_user.username}".')
        messages.success(request, f'Password for {target_user.username} has been changed.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_change_password.html', {
        'target_user': target_user,
        'is_fixed_admin': is_fixed,
    })


@admin_required
@require_http_methods(['GET', 'POST'])
def user_edit(request, pk):
    """Edit staff username and full name. Not allowed for the fixed admin."""
    target_user = get_object_or_404(User, pk=pk)
    if is_fixed_admin_user(target_user):
        messages.error(request, 'The fixed admin account cannot be edited.')
        return redirect('administrator:user_accounts')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        if not username:
            messages.error(request, 'Username is required.')
            return render(request, 'administrator/user_edit.html', {'target_user': target_user})

        if User.objects.filter(username__iexact=username).exclude(pk=target_user.pk).exists():
            messages.error(request, 'That username is already taken.')
            return render(request, 'administrator/user_edit.html', {'target_user': target_user})

        target_user.username = username
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.save()
        log_activity(request, UserActivity.ACTION_UPDATE, f'Updated user "{username}".')
        messages.success(request, f'User "{username}" updated.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_edit.html', {'target_user': target_user})


@admin_required
def user_activity(request):
    """User activity logs – show real activity from UserActivity model."""
    activities = UserActivity.objects.select_related('user').all()[:500]
    return render(request, 'administrator/user_activity.html', {'activities': activities})


@admin_required
@require_http_methods(['GET', 'POST'])
def user_delete(request, pk):
    """
    Admin only: delete a Staff user.
    The fixed admin account and Admin-role users cannot be deleted here.
    """
    target_user = get_object_or_404(User, pk=pk)

    if is_fixed_admin_user(target_user) or user_is_admin(target_user):
        messages.error(request, 'Admin accounts cannot be deleted from here. Only Staff users can be deleted.')
        return redirect('administrator:user_accounts')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        log_activity(request, UserActivity.ACTION_DELETE, f'Deleted user "{username}".')
        messages.success(request, f'User "{username}" has been deleted.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_delete.html', {'target_user': target_user})
