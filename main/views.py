"""Common views for the main app (e.g. auth)."""
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core import signing
from django.urls import reverse
from urllib.parse import urlencode
import secrets
from django.contrib.auth.views import LoginView

from administrator.models import PasswordChangeRequest
from administrator.models import UserActivity
from administrator.models import AdminOTP
from administrator.models import SentEmail
from administrator.activity_log import log_activity_for_user
from administrator.email_utils import send_and_log_email
from administrator.utils import ADMIN_GROUP_NAME

User = get_user_model()


def sign_out(request):
    """Sign out the user. Accepts both GET and POST so links and forms work."""
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


@require_http_methods(['GET', 'POST'])
def password_reset_request(request):
    """User requests password change. Admin confirms, then new password is sent to user's email."""
    if request.method == 'POST':
        username = (request.POST.get('username', '') or '').strip()
        if not username:
            messages.error(request, 'Please enter your username.')
            return render(request, 'registration/password_reset_form.html')

        user = User.objects.filter(username__iexact=username).first()
        if user:
            email = (user.email or '').strip()
            if not email:
                messages.error(request, 'No email on file for this account. Contact your administrator.')
                return render(request, 'registration/password_reset_form.html')

            # Create pending request; admin will confirm and send
            if not PasswordChangeRequest.objects.filter(user=user, status=PasswordChangeRequest.STATUS_PENDING).exists():
                PasswordChangeRequest.objects.create(user=user)
            log_activity_for_user(
                user=user,
                request=request,
                action=UserActivity.ACTION_FORGOT_PASSWORD,
                description='User submitted a forgot password request',
            )

        # Don't reveal whether account exists; always show same message
        return redirect('password_reset_done')

    return render(request, 'registration/password_reset_form.html')


def password_reset_done(request):
    """Show 'request submitted' – admin will confirm and send new password to email."""
    return render(request, 'registration/password_reset_done.html')


def _is_admin_user(user):
    if not user:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    try:
        return user.groups.filter(name=ADMIN_GROUP_NAME).exists()
    except Exception:
        return False


class RoleLoginView(LoginView):
    """
    Single login endpoint with two forms on the template:
    - Admin Login: only Admin users allowed
    - User Login: only non-Admin users allowed
    """
    template_name = 'registration/login.html'

    def form_valid(self, form):
        login_type = (self.request.POST.get('login_type') or '').strip().lower()
        user = form.get_user()

        # Enforce role before we log the user in.
        if login_type == 'admin' and not _is_admin_user(user):
            form.add_error(None, 'This form is for Admin accounts only. Please use User Login.')
            return self.form_invalid(form)
        if login_type == 'user' and _is_admin_user(user):
            form.add_error(None, 'This form is for User accounts only. Please use Admin Login.')
            return self.form_invalid(form)

        return super().form_valid(form)


@require_http_methods(['GET', 'POST'])
def admin_password_reset_request(request):
    """
    Admin self-service forgot password.
    Sends a 4-digit OTP to the admin's email, then redirects to verify page.
    """
    if request.method == 'POST':
        username = (request.POST.get('username', '') or '').strip()
        if not username:
            messages.error(request, 'Please enter your username.')
            return render(request, 'registration/admin_password_reset_form.html')

        user = User.objects.filter(username__iexact=username).first()
        if user and _is_admin_user(user) and (user.email or '').strip():
            # Create OTP (10 minutes)
            code = f'{secrets.randbelow(10000):04d}'
            AdminOTP.objects.create(
                admin=user,
                purpose=AdminOTP.PURPOSE_PASSWORD_CHANGE,
                code_hash=make_password(code),
                expires_at=timezone.now() + timezone.timedelta(minutes=10),
                related_user=user,
            )

            body = (
                f'Hello {user.get_full_name() or user.username},\n\n'
                f'Your OTP for admin password reset is:\n\n'
                f'OTP: {code}\n\n'
                f'This code will expire in 10 minutes.\n\n'
                f'— Profiling System'
            )
            send_and_log_email(
                recipient_email=(user.email or '').strip(),
                subject='Admin password reset OTP – Profiling System',
                body_plain=body,
                email_type=SentEmail.TYPE_OTHER,
                sent_by=None,
                related_user=user,
            )

            token = signing.dumps({'u': user.pk}, salt='admin-password-reset')
            # Generic success message, but continue flow for valid admin
            url = reverse('admin_password_reset_verify')
            return redirect(f'{url}?{urlencode({"token": token})}')

        # Always respond the same way to avoid leaking account existence.
        messages.success(request, 'If the admin account exists, an OTP has been sent to its email.')
        return redirect('login')

    return render(request, 'registration/admin_password_reset_form.html')


@require_http_methods(['GET', 'POST'])
def admin_password_reset_verify(request):
    """Verify OTP and set a new admin password."""
    token = (request.GET.get('token', '') or '').strip()
    if not token:
        return redirect('admin_password_reset')

    try:
        payload = signing.loads(token, salt='admin-password-reset', max_age=60 * 30)
        user_id = int(payload.get('u'))
    except Exception:
        messages.error(request, 'This reset link is invalid or expired. Please request a new OTP.')
        return redirect('admin_password_reset')

    user = User.objects.filter(pk=user_id).first()
    if not (user and _is_admin_user(user) and (user.email or '').strip()):
        messages.error(request, 'This reset link is invalid. Please request a new OTP.')
        return redirect('admin_password_reset')

    if request.method == 'POST':
        otp = (request.POST.get('otp') or '').strip()
        new_password = (request.POST.get('new_password') or '')
        new_password_confirm = (request.POST.get('new_password_confirm') or '')

        if not (otp.isdigit() and len(otp) == 4):
            messages.error(request, 'OTP is required (4 digits).')
            return render(request, 'registration/admin_password_reset_verify.html', {'token': token})

        if not new_password or len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'registration/admin_password_reset_verify.html', {'token': token})
        if new_password != new_password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/admin_password_reset_verify.html', {'token': token})

        otp_row = (
            AdminOTP.objects.filter(
                admin=user,
                purpose=AdminOTP.PURPOSE_PASSWORD_CHANGE,
                related_user=user,
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
            messages.error(request, 'Invalid or expired OTP. Please request a new OTP.')
            return render(request, 'registration/admin_password_reset_verify.html', {'token': token})

        otp_row.consumed_at = timezone.now()
        otp_row.save(update_fields=['consumed_at'])

        user.set_password(new_password)
        user.save()
        log_activity_for_user(
            user=user,
            request=request,
            action=UserActivity.ACTION_FORGOT_PASSWORD,
            description='Admin reset password via email OTP',
        )

        messages.success(request, 'Password updated. You can sign in now.')
        return redirect('login')

    return render(request, 'registration/admin_password_reset_verify.html', {'token': token})
