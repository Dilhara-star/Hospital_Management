from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.shortcuts import redirect  # helper to send the user to another page


def require_role(request, allowed_roles, message='You do not have permission to view this page.', redirect_to='dashboard_index'):
    # checks if the logged in user's profile role is inside the allowed_roles list.
    # call this at the top of a view, like: error_response = require_role(request, ['admin', 'doctor'])
    # returns a redirect when the role is not allowed, or None when the view may continue.
    if not hasattr(request.user, 'profile') or request.user.profile.role not in allowed_roles:
        messages.error(request, message)  # show why the page was blocked
        return redirect(redirect_to)  # send them somewhere safe
    return None
