"""Common views for the main app (e.g. auth)."""
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect


def sign_out(request):
    """Sign out the user. Accepts both GET and POST so links and forms work."""
    logout(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)
