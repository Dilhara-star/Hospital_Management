from django.shortcuts import render  # helper to render a page


# shows the "About Us" page; open to everyone, no login needed
def about_us(request):
    return render(request, 'frontend/core/about.html')


# shows the "Terms of Service" page; open to everyone, no login needed
def terms_of_service(request):
    return render(request, 'frontend/core/tos.html')


# shows the "Privacy Policy" page; open to everyone, no login needed
def privacy_policy(request):
    return render(request, 'frontend/core/privacy_policy.html')
