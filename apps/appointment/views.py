from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import AppointmentForm


@login_required
def appointment_form(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()
            messages.success(request, 'Your appointment has been scheduled. Thank you!')
            return redirect('appointment_form')
    else:
        form = AppointmentForm()
    return render(request, 'frontend/appointment/form.html', {'form': form})
