from django.shortcuts import render  # helper to render a page
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in


# shows the "About Us" page; only logged in users may view it
@login_required
def about_us(request):
    return render(request, 'frontend/core/about.html')
