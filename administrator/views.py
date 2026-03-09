from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
import secrets

from .models import UserProfile, UserActivity, SentEmail, PasswordChangeRequest, AdminOTP
from .utils import ADMIN_GROUP_NAME, STAFF_GROUP_NAME, user_is_admin, is_fixed_admin_user, get_fixed_admin_username
from .activity_log import log_activity
from .email_utils import send_and_log_email

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
def sent_emails(request):
    """List sent emails and pending password change requests. Admin can approve/reject from here."""
    # Handle approve/reject for password change requests
    if request.method == 'POST':
        approve_id = request.POST.get('approve_id')
        if approve_id:
            req = get_object_or_404(PasswordChangeRequest, pk=approve_id, status=PasswordChangeRequest.STATUS_PENDING)
            user = req.user
            user_email = (user.email or '').strip()
            if not user_email:
                messages.error(request, f'User {user.username} has no email. Add email in User Edit first.')
                return redirect('administrator:sent_emails')

            otp = (request.POST.get('otp') or '').strip()
            if not (otp.isdigit() and len(otp) == 4):
                messages.error(request, 'OTP is required (4 digits). Click "Set new password" again to resend OTP if needed.')
                return redirect('administrator:sent_emails')

            otp_row = (
                AdminOTP.objects.filter(
                    admin=request.user,
                    purpose=AdminOTP.PURPOSE_PASSWORD_REQUEST_APPROVAL,
                    related_request=req,
                    consumed_at__isnull=True,
                    expires_at__gt=timezone.now(),
                )
                .order_by('-created_at')
                .first()
            )
            if not otp_row or not check_password(otp, otp_row.code_hash):
                if otp_row:
                    otp_row.attempts = min((otp_row.attempts or 0) + 1, 999)
                    otp_row.save(update_fields=['attempts'])
                messages.error(request, 'Invalid or expired OTP. Please resend OTP and try again.')
                return redirect('administrator:sent_emails')

            otp_row.consumed_at = timezone.now()
            otp_row.save(update_fields=['consumed_at'])

            new_password = (request.POST.get('new_password') or '').strip()
            new_password_confirm = (request.POST.get('new_password_confirm') or '').strip()
            if not new_password or len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return redirect('administrator:sent_emails')
            if new_password != new_password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('administrator:sent_emails')

            user.set_password(new_password)
            user.save()

            body = (
                f'Hello {user.get_full_name() or user.username},\n\n'
                f'Your password change request has been approved. Here are your new login details:\n\n'
                f'Username: {user.username}\n'
                f'New password: {new_password}\n\n'
                f'Please sign in and change your password after logging in if you wish.\n\n'
                f'— Profiling System'
            )
            if send_and_log_email(
                recipient_email=user_email,
                subject='Your new password – Profiling System',
                body_plain=body,
                email_type=SentEmail.TYPE_PASSWORD_RESET,
                sent_by=request.user,
                related_user=user,
            ):
                req.status = PasswordChangeRequest.STATUS_APPROVED
                req.processed_at = timezone.now()
                req.processed_by = request.user
                req.save()
                log_activity(request, UserActivity.ACTION_UPDATE, f'Approved password change for {user.username}, sent new password to email.')
                messages.success(request, f'New password sent to {user.username} ({user_email}).')
            else:
                messages.error(request, 'Failed to send email. Please try again.')

        reject_id = request.POST.get('reject_id')
        if reject_id:
            req = get_object_or_404(PasswordChangeRequest, pk=reject_id, status=PasswordChangeRequest.STATUS_PENDING)
            req.status = PasswordChangeRequest.STATUS_REJECTED
            req.processed_at = timezone.now()
            req.processed_by = request.user
            req.save()
            log_activity(request, UserActivity.ACTION_UPDATE, f'Rejected password change request for {req.user.username}.')
            messages.success(request, 'Request rejected.')

        return redirect('administrator:sent_emails')

    emails = SentEmail.objects.select_related('sent_by', 'related_user').order_by('-sent_at')[:200]
    pending_requests = PasswordChangeRequest.objects.filter(status=PasswordChangeRequest.STATUS_PENDING).select_related('user').order_by('-requested_at')

    # Combined list: requests first (as "items"), then emails - all in Email Log
    items = []
    for req in pending_requests:
        items.append({'type': 'request', 'request': req, 'date': req.requested_at})
    for em in emails:
        items.append({'type': 'email', 'email': em, 'date': em.sent_at})
    items.sort(key=lambda x: x['date'], reverse=True)

    return render(request, 'administrator/sent_emails.html', {'items': items})


@admin_required
@require_http_methods(['POST'])
def password_request_send_otp(request, pk):
    """Send a 4-digit OTP to the admin's email for approving a password request."""
    req = get_object_or_404(PasswordChangeRequest, pk=pk, status=PasswordChangeRequest.STATUS_PENDING)

    admin_email = (request.user.email or '').strip()
    if not admin_email:
        messages.error(request, 'Your admin account has no email set. Add an email first, then try again.')
        return redirect('administrator:sent_emails')

    code = f'{secrets.randbelow(10000):04d}'
    expires_at = timezone.now() + timezone.timedelta(minutes=10)

    AdminOTP.objects.create(
        admin=request.user,
        purpose=AdminOTP.PURPOSE_PASSWORD_REQUEST_APPROVAL,
        code_hash=make_password(code),
        expires_at=expires_at,
        related_request=req,
        related_user=req.user,
    )

    body = (
        f'Hello {request.user.get_full_name() or request.user.username},\n\n'
        f'Your OTP for approving a password reset request is:\n\n'
        f'OTP: {code}\n\n'
        f'This code will expire in 10 minutes.\n\n'
        f'— Profiling System'
    )
    ok = send_and_log_email(
        recipient_email=admin_email,
        subject='OTP Code – Profiling System',
        body_plain=body,
        email_type=SentEmail.TYPE_OTHER,
        sent_by=request.user,
        related_user=req.user,
    )
    if ok:
        messages.success(request, f'OTP sent to {admin_email}.')
    else:
        messages.error(request, 'Failed to send OTP email. Please check email settings and try again.')
    return redirect('administrator:sent_emails')


@admin_required
def mark_request_read(request, pk):
    """Mark a password change request as read. Uses GET to avoid CSRF for fetch."""
    from django.http import JsonResponse
    from django.utils import timezone
    req = get_object_or_404(PasswordChangeRequest, pk=pk, status=PasswordChangeRequest.STATUS_PENDING)
    req.read_at = timezone.now()
    req.save()
    return JsonResponse({'ok': True})


@admin_required
def sent_email_view(request, pk):
    """Return email detail as JSON for the view modal."""
    from django.http import JsonResponse
    email = get_object_or_404(SentEmail, pk=pk)
    return JsonResponse({
        'subject': email.subject,
        'recipient_email': email.recipient_email,
        'sent_at': email.sent_at.strftime('%Y-%m-%d %H:%M:%S'),
        'email_type': email.get_email_type_display(),
        'body_plain': email.body_plain or '',
        'sent_by': email.sent_by.get_full_name() or email.sent_by.username if email.sent_by else '',
        'related_user': email.related_user.username if email.related_user else '',
    })


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
        # Area delete flags (legacy – still supported if you keep them in the form)
        can_ops = request.POST.get('can_delete_in_operations') == 'on'
        can_ref = request.POST.get('can_delete_in_reference') == 'on'

        # Section-level toggles
        manage_ref_all = request.POST.get('can_manage_reference') == 'on'
        manage_ref_barangay = request.POST.get('can_manage_reference_barangay') == 'on'
        manage_ref_position = request.POST.get('can_manage_reference_position') == 'on'

        manage_ops_all = request.POST.get('can_manage_operations') == 'on'
        manage_ops_coord = request.POST.get('can_manage_operations_coordinator') == 'on'
        manage_ops_bo = request.POST.get('can_manage_operations_barangay_official') == 'on'
        manage_ops_res = request.POST.get('can_manage_operations_residents_record') == 'on'
        manage_ops_voters = request.POST.get('can_manage_operations_voters_registration') == 'on'

        # Fine-grained actions per subsection
        # Reference → Barangay
        add_ref_barangay = request.POST.get('can_add_reference_barangay') == 'on'
        edit_ref_barangay = request.POST.get('can_edit_reference_barangay') == 'on'
        delete_ref_barangay = request.POST.get('can_delete_reference_barangay') == 'on'

        # Reference → Position
        add_ref_position = request.POST.get('can_add_reference_position') == 'on'
        edit_ref_position = request.POST.get('can_edit_reference_position') == 'on'
        delete_ref_position = request.POST.get('can_delete_reference_position') == 'on'

        # Operations → Coordinator
        add_ops_coord = request.POST.get('can_add_operations_coordinator') == 'on'
        edit_ops_coord = request.POST.get('can_edit_operations_coordinator') == 'on'
        delete_ops_coord = request.POST.get('can_delete_operations_coordinator') == 'on'

        # Operations → Barangay Official
        add_ops_bo = request.POST.get('can_add_operations_barangay_official') == 'on'
        edit_ops_bo = request.POST.get('can_edit_operations_barangay_official') == 'on'
        delete_ops_bo = request.POST.get('can_delete_operations_barangay_official') == 'on'

        # Operations → Residents Record
        add_ops_res = request.POST.get('can_add_operations_residents_record') == 'on'
        edit_ops_res = request.POST.get('can_edit_operations_residents_record') == 'on'
        delete_ops_res = request.POST.get('can_delete_operations_residents_record') == 'on'

        # Operations → Voters Registration
        add_ops_voters = request.POST.get('can_add_operations_voters_registration') == 'on'
        edit_ops_voters = request.POST.get('can_edit_operations_voters_registration') == 'on'
        delete_ops_voters = request.POST.get('can_delete_operations_voters_registration') == 'on'

        if admin_group and staff_group:
            if role == 'admin':
                user.groups.remove(staff_group)
                user.groups.add(admin_group)
            else:
                user.groups.remove(admin_group)
                user.groups.add(staff_group)

        profile.can_delete_in_operations = can_ops
        profile.can_delete_in_reference = can_ref
        profile.can_manage_reference = manage_ref_all
        profile.can_manage_reference_barangay = manage_ref_barangay
        profile.can_manage_reference_position = manage_ref_position
        profile.can_manage_operations = manage_ops_all
        profile.can_manage_operations_coordinator = manage_ops_coord
        profile.can_manage_operations_barangay_official = manage_ops_bo
        profile.can_manage_operations_residents_record = manage_ops_res
        profile.can_manage_operations_voters_registration = manage_ops_voters

        profile.can_add_reference_barangay = add_ref_barangay
        profile.can_edit_reference_barangay = edit_ref_barangay
        profile.can_delete_reference_barangay = delete_ref_barangay

        profile.can_add_reference_position = add_ref_position
        profile.can_edit_reference_position = edit_ref_position
        profile.can_delete_reference_position = delete_ref_position

        profile.can_add_operations_coordinator = add_ops_coord
        profile.can_edit_operations_coordinator = edit_ops_coord
        profile.can_delete_operations_coordinator = delete_ops_coord

        profile.can_add_operations_barangay_official = add_ops_bo
        profile.can_edit_operations_barangay_official = edit_ops_bo
        profile.can_delete_operations_barangay_official = delete_ops_bo

        profile.can_add_operations_residents_record = add_ops_res
        profile.can_edit_operations_residents_record = edit_ops_res
        profile.can_delete_operations_residents_record = delete_ops_res

        profile.can_add_operations_voters_registration = add_ops_voters
        profile.can_edit_operations_voters_registration = edit_ops_voters
        profile.can_delete_operations_voters_registration = delete_ops_voters
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

        otp = (request.POST.get('otp') or '').strip()
        if not (otp.isdigit() and len(otp) == 4):
            messages.error(request, 'OTP is required (4 digits). Click "Send OTP" first.')
            return render(request, 'administrator/user_change_password.html', {
                'target_user': target_user,
                'is_fixed_admin': is_fixed,
            })

        otp_row = (
            AdminOTP.objects.filter(
                admin=request.user,
                purpose=AdminOTP.PURPOSE_PASSWORD_CHANGE,
                related_user=target_user,
                consumed_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .order_by('-created_at')
            .first()
        )
        if not otp_row or not check_password(otp, otp_row.code_hash):
            if otp_row:
                otp_row.attempts = min((otp_row.attempts or 0) + 1, 999)
                otp_row.save(update_fields=['attempts'])
            messages.error(request, 'Invalid or expired OTP. Please resend OTP and try again.')
            return render(request, 'administrator/user_change_password.html', {
                'target_user': target_user,
                'is_fixed_admin': is_fixed,
            })

        otp_row.consumed_at = timezone.now()
        otp_row.save(update_fields=['consumed_at'])

        target_user.set_password(new_password)
        target_user.save()
        log_activity(request, UserActivity.ACTION_UPDATE, f'Changed password for user "{target_user.username}".')

        # Send email notification to the user whose password was changed
        user_email = (target_user.email or '').strip()
        if user_email:
            email_body = (
                f'Hello {target_user.get_full_name() or target_user.username},\n\n'
                f'Your password for the Profiling System has been changed by an administrator.\n\n'
                f'Username: {target_user.username}\n\n'
                f'If you did not request this change, please contact your administrator immediately.\n\n'
                f'— Profiling System'
            )
            send_and_log_email(
                recipient_email=user_email,
                subject='Your Profiling System password has been changed',
                body_plain=email_body,
                email_type=SentEmail.TYPE_PASSWORD_CHANGE,
                sent_by=request.user,
                related_user=target_user,
            )

        messages.success(request, f'Password for {target_user.username} has been changed.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_change_password.html', {
        'target_user': target_user,
        'is_fixed_admin': is_fixed,
    })


@admin_required
@require_http_methods(['POST'])
def user_change_password_send_otp(request, pk):
    """Send a 4-digit OTP to the admin's email for changing a user's password."""
    if not user_is_admin(request.user):
        messages.error(request, 'You do not have permission to change passwords.')
        return redirect('administrator:user_accounts')

    target_user = get_object_or_404(User, pk=pk)
    admin_email = (request.user.email or '').strip()
    if not admin_email:
        messages.error(request, 'Your admin account has no email set. Add an email first, then try again.')
        return redirect('administrator:user_change_password', pk=pk)

    code = f'{secrets.randbelow(10000):04d}'
    expires_at = timezone.now() + timezone.timedelta(minutes=10)
    AdminOTP.objects.create(
        admin=request.user,
        purpose=AdminOTP.PURPOSE_PASSWORD_CHANGE,
        code_hash=make_password(code),
        expires_at=expires_at,
        related_user=target_user,
    )

    body = (
        f'Hello {request.user.get_full_name() or request.user.username},\n\n'
        f'Your OTP for changing a user password is:\n\n'
        f'OTP: {code}\n\n'
        f'This code will expire in 10 minutes.\n\n'
        f'— Profiling System'
    )
    ok = send_and_log_email(
        recipient_email=admin_email,
        subject='OTP Code – Profiling System',
        body_plain=body,
        email_type=SentEmail.TYPE_OTHER,
        sent_by=request.user,
        related_user=target_user,
    )
    if ok:
        messages.success(request, f'OTP sent to {admin_email}.')
    else:
        messages.error(request, 'Failed to send OTP email. Please check email settings and try again.')
    return redirect('administrator:user_change_password', pk=pk)


@admin_required
@require_http_methods(['GET', 'POST'])
def user_edit(request, pk):
    """Edit user: username, full name, and email. For fixed admin, only email and name can be edited (not username)."""
    target_user = get_object_or_404(User, pk=pk)
    is_fixed = is_fixed_admin_user(target_user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        if not is_fixed and not username:
            messages.error(request, 'Username is required.')
            return render(request, 'administrator/user_edit.html', {'target_user': target_user, 'is_fixed_admin': is_fixed})

        if not is_fixed and User.objects.filter(username__iexact=username).exclude(pk=target_user.pk).exists():
            messages.error(request, 'That username is already taken.')
            return render(request, 'administrator/user_edit.html', {'target_user': target_user, 'is_fixed_admin': is_fixed})

        if not is_fixed:
            target_user.username = username
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email
        target_user.save()
        log_activity(request, UserActivity.ACTION_UPDATE, f'Updated user "{target_user.username}".')
        messages.success(request, f'User "{target_user.username}" updated.')
        return redirect('administrator:user_accounts')

    return render(request, 'administrator/user_edit.html', {'target_user': target_user, 'is_fixed_admin': is_fixed})


@admin_required
def user_activity(request):
    """User activity logs – show real activity from UserActivity model."""
    activities_qs = UserActivity.objects.select_related('user').all()

    # Filters from query params
    username = request.GET.get('user') or ''
    action = request.GET.get('action') or ''
    date_str = request.GET.get('date') or ''

    if username:
        activities_qs = activities_qs.filter(user__username=username)

    if action:
        activities_qs = activities_qs.filter(action=action)

    if date_str:
        # HTML date input typically sends YYYY-MM-DD; keep it simple and safe
        from datetime import datetime

        try:
            # Try ISO format (default for type="date")
            day = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Fallback to MM/DD/YYYY if manually typed
                day = datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                day = None

        if day:
            activities_qs = activities_qs.filter(created_at__date=day)

    activities = activities_qs[:500]

    # Distinct users and actions for dropdowns
    user_list = (
        User.objects.filter(activity_logs__isnull=False)
        .distinct()
        .order_by('username')
    )
    action_choices = UserActivity.ACTION_CHOICES

    context = {
        'activities': activities,
        'filter_user': username,
        'filter_action': action,
        'filter_date': date_str,
        'activity_users': user_list,
        'activity_actions': action_choices,
    }

    return render(request, 'administrator/user_activity.html', context)


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
