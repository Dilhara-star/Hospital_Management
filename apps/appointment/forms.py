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

    # stops a patient from booking an appointment on a date that has already passed
    def clean_date(self):
        appointment_date = self.cleaned_data['date']
        if appointment_date < date.today():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return appointment_date


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

    # stops a patient from rescheduling their appointment into the past
    def clean_date(self):
        # stop the patient from rescheduling into the past
        new_date = self.cleaned_data['date']
        if new_date < date.today():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return new_date
