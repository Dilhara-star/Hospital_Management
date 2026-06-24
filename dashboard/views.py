from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def dashboard_index(request):
    return render(request, 'dashboard/index.html')


def login_view(request):
    # If the user is already authenticated, redirect them to the dashboard index
    if request.user.is_authenticated:
        return redirect('dashboard_index')

    # If the request method is POST, authenticate the user
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        
        # If the user is authenticated, log them in and redirect them to the dashboard index
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard_index'))
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')
