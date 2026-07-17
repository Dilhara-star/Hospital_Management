from datetime import date

from django import forms
from django.contrib.auth.models import User

from .models import Appointment, Payment


class UserChoiceField(forms.ModelChoiceField):
    # shows a person's full name in the dropdown instead of their username
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class AppointmentForm(forms.ModelForm):
    doctor = UserChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        empty_label='Select Doctor',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Appointment
        # fields shown on the form, in the order they should appear
        fields = [
            'department', 'date', 'time_slot', 'doctor', 'message',
            'patient_name', 'patient_contact', 'patient_age', 'patient_address', 'patient_nic',
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-select'}),  # dropdown of fixed time slots
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Additional notes or symptoms (optional)',
            }),
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'patient_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age', 'min': 0}),
            'patient_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Home address'}),
            'patient_nic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIC number'}),
        }

    def clean_date(self):
        appointment_date = self.cleaned_data['date']
        if appointment_date < date.today():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return appointment_date


class StaffAppointmentForm(forms.ModelForm):
    # used on the dashboard "Add Appointment" and "Edit Appointment" pages,
    # where staff pick which patient the appointment is for and can set its status
    patient = UserChoiceField(
        queryset=User.objects.filter(profile__role='patient', is_active=True).order_by('first_name', 'last_name'),
        empty_label='Select Patient',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    doctor = UserChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        empty_label='Select Doctor',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Appointment
        # fields shown on the form, in the order they should appear
        fields = [
            'patient', 'department', 'date', 'time_slot', 'doctor', 'message', 'status',
            'patient_name', 'patient_contact', 'patient_age', 'patient_address', 'patient_nic',
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),  # dropdown of fixed time slots
            'status': forms.Select(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_age': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'patient_address': forms.TextInput(attrs={'class': 'form-control'}),
            'patient_nic': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PaymentForm(forms.ModelForm):
    # used on the "Edit Appointment" page, so staff can correct the payment details
    class Meta:
        model = Payment
        fields = ['amount', 'method', 'status']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
