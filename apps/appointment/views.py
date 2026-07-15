from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Appointment
from .forms import AppointmentForm

@login_required
def appointment_index(request):
    appointments = Appointment.objects.all()
    return render(request, 'dashboard/appointment_management/index.html', {'appointments': appointments})



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

def appointment_view(request, pk):
    appointment = Appointment.objects.get(pk=pk)
    print(appointment)
    return render(request, 'dashboard/appointment_management/view.html', {'appointment': appointment})

def appointment_delete(request, pk):
    appointment = Appointment.objects.get(pk=pk)
    appointment.delete()
    messages.success(request, 'Your appointment has been deleted.')
    return redirect('appointment_index')