from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """
    Decorator that restricts access to staff and superuser accounts.
    Redirects unauthenticated users to the login page and unauthorised
    users to the home page with an error message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'You do not have permission to access the admin panel.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
