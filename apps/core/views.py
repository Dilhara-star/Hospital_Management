from django.shortcuts import render  # helper to render a page


# shows the "About Us" page; open to everyone, no login needed
def about_us(request):
    return render(request, 'frontend/core/about.html')
