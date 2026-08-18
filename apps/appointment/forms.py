from datetime import date

from django import forms
from django.contrib.auth.models import User

from .models import Appointment, Payment


# form to check a patient's own booking is valid; the view saves the fields by hand
class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        required=False,
    )

    class Meta:
        model = Appointment
        # fields checked by this form, in the order they appear on the booking page
        fields = [
            'department', 'date', 'time_slot', 'doctor', 'message',
            'patient_name', 'patient_contact', 'patient_age', 'patient_address', 'patient_nic',
        ]


# form to check a staff-registered appointment is valid; the view saves the fields by hand
class StaffAppointmentForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='patient', is_active=True).order_by('first_name', 'last_name'),
    )
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        required=False,
    )

    class Meta:
        model = Appointment
        # fields checked by this form, in the order they appear on the dashboard add/edit page
        fields = [
            'patient', 'department', 'date', 'time_slot', 'doctor', 'message', 'status',
            'patient_name', 'patient_contact', 'patient_age', 'patient_address', 'patient_nic',
        ]


# form to check the payment fields on the dashboard "Edit Appointment" page are valid
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'status']


# used on the patient's "My Appointments" page, only to check the new date/time slot are
# valid before the view saves them by hand; the html page draws its own plain input boxes
class AppointmentEditForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time_slot']

    # stops a patient rescheduling into a slot their doctor is already booked for
    def clean(self):
        cleaned_data = super().clean()  # run the normal field checks first
        appointment_date = cleaned_data.get('date')  # new date picked on the form
        time_slot = cleaned_data.get('time_slot')  # new time slot picked on the form
        doctor = self.instance.doctor  # the doctor is not changed on this form, so read it from the instance

        if doctor and appointment_date and time_slot:  # only checkable once all three are known
            clash = Appointment.objects.filter(
                doctor=doctor, date=appointment_date, time_slot=time_slot,
            ).exclude(status='cancelled').exclude(pk=self.instance.pk)  # a cancelled slot is free, and skip itself
            if clash.exists():  # someone else already has this doctor booked at this time
                self.add_error('time_slot', 'This doctor is already booked for that date and time slot. Please pick another slot.')

        return cleaned_data
