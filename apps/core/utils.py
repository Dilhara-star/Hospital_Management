from functools import wraps  # keeps the view's real name and docstring after we wrap it
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.shortcuts import redirect  # helper to send the user to another page


def required_role(allowed_roles, message='You do not have permission to view this page.', redirect_to='dashboard_index'):
    # a decorator - put it under @login_required, like this:
    #   @login_required
    #   @required_role(['admin', 'doctor'])
    #   def my_view(request):
    #       ...
    # only lets the view run if the logged in user's profile role is inside allowed_roles
    def decorator(view_func):
        @wraps(view_func)  # keeps the view's real name and docstring
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile') or request.user.profile.role not in allowed_roles:
                messages.error(request, message)  # show why the page was blocked
                return redirect(redirect_to)  # send them somewhere safe
            return view_func(request, *args, **kwargs)  # role is allowed, so run the real view
        return wrapped_view
    return decorator
