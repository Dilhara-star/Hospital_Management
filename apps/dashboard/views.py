from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def dashboard_index(request):
    return render(request, 'dashboard/index.html')


def _redirect_by_role(user):
    """Route patients to patient portal, regular users to frontend, staff to dashboard."""
    if hasattr(user, 'profile'):
        role = user.profile.role
        if role == 'patient':
            return redirect('patient_portal')
        if role == 'user':
            return redirect('frontend_index')
    return redirect('dashboard_index')


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')
