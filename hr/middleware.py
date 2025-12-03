"""
Custom middleware for authentication and error handling.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse


class AuthenticationMiddleware:
    """Enforce authentication on dashboard routes"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_paths = ['/dashboard/']

    def __call__(self, request):
        # Check if path is protected
        if any(request.path.startswith(path) for path in self.protected_paths):
            if not request.user.is_authenticated:
                return redirect(f'/admin/login/?next={request.path}')

        response = self.get_response(request)
        return response
