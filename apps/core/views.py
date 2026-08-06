from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


@login_required
def about_us(request):
    return render(request, 'frontend/core/about.html')


@login_required
def contact_us(request):
    return render(request, 'frontend/core/contact.html')

# Create your views here.
