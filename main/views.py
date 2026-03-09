"""Common views for the main app (e.g. auth)."""
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from administrator.models import PasswordChangeRequest

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

        # Don't reveal whether account exists; always show same message
        return redirect('password_reset_done')

    return render(request, 'registration/password_reset_form.html')


def password_reset_done(request):
    """Show 'request submitted' – admin will confirm and send new password to email."""
    return render(request, 'registration/password_reset_done.html')
