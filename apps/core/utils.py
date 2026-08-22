import re  # used to check a phone number is made up of digits only
from functools import wraps  # keeps the view's real name and docstring after we wrap it
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.core.exceptions import ValidationError  # raised when a form field fails a check
from django.shortcuts import redirect  # helper to send the user to another page

# a valid phone number: digits only, with an optional + at the very start, 7 to 15 digits long
PHONE_PATTERN = re.compile(r'^\+?\d{7,15}$')

# a valid Sri Lankan NIC: old format is 9 digits then V or X, new format is 12 digits
NIC_PATTERN = re.compile(r'^([0-9]{9}[VXvx]|[0-9]{12})$')

# picture file extensions allowed for profile pictures
ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
# largest a profile picture file is allowed to be, in bytes (5 MB)
MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024


# checks a phone number typed on a form is a sensible shape; raises an error if not
def check_phone_number(value):
    # skip the check if the field was left blank (forms already handle "required" separately)
    if value and not PHONE_PATTERN.match(value):
        raise ValidationError('Enter a valid phone number (digits only, 7 to 15 numbers long).')


# checks a Sri Lankan NIC number typed on a form is a sensible shape; raises an error if not
def check_nic_number(value):
    # skip the check if the field was left blank (forms already handle "required" separately)
    if value and not NIC_PATTERN.match(value):
        raise ValidationError('Enter a valid NIC number (9 digits followed by V/X, or 12 digits).')


# checks an uploaded picture file is a sensible size and a real image type; raises an error if not
def check_image_file(file):
    # skip the check if no file was uploaded
    if not file:
        return
    # stop if the file is bigger than the allowed size
    if file.size > MAX_IMAGE_FILE_SIZE:
        raise ValidationError('Image file must be smaller than 5 MB.')
    # stop if the file name doesn't end in an allowed image extension
    if not file.name.lower().endswith(ALLOWED_IMAGE_EXTENSIONS):
        raise ValidationError('Image must be a JPG, PNG, or WEBP file.')


# blocks a view unless the logged in user's profile role is in the allowed list
def required_role(allowed_roles, message='You do not have permission to view this page.', redirect_to='dashboard_index'):
    # a decorator - put it under @login_required, like this:
    #   @login_required
    #   @required_role(['admin', 'doctor'])
    #   def my_view(request):
    #       ...
    # only lets the view run if the logged in user's profile role is inside allowed_roles
    def decorator(view_func):
        # runs the role check, then either blocks the request or runs the real view
        @wraps(view_func)  # keeps the view's real name and docstring
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile') or request.user.profile.role not in allowed_roles:
                messages.error(request, message)  # show why the page was blocked
                return redirect(redirect_to)  # send them somewhere safe
            return view_func(request, *args, **kwargs)  # role is allowed, so run the real view
        return wrapped_view
    return decorator
