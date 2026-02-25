"""Middleware to require login for all views except sign-in, sign-out, and admin."""
from django.shortcuts import redirect
from django.conf import settings
class LoginRequiredMiddleware:
    """
    Redirect unauthenticated users to the login page for any URL
    except login, logout, admin, and static.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path
            # Allow login, logout, admin, static
            login_url = getattr(settings, 'LOGIN_URL', '/sign-in/').rstrip('/')
            if path.rstrip('/') == login_url:
                return self.get_response(request)
            if path == '/sign-out/':
                return self.get_response(request)
            if path.startswith('/admin/'):
                return self.get_response(request)
            if path.startswith('/static/'):
                return self.get_response(request)
            if path == '/favicon.ico':
                return self.get_response(request)
            return redirect(settings.LOGIN_URL + '?next=' + request.get_full_path())
        return self.get_response(request)
