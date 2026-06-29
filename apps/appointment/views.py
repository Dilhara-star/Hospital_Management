from django.shortcuts import render

# Create your views here.
def appointment_form(request):
    return render(request, 'frontend/appointment/form.html')