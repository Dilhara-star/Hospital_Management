from datetime import date

from django import forms
from django.contrib.auth.models import User

from apps.core.utils import check_phone_number, check_nic_number  # checks a phone number and a NIC number are sensible
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


# form to check a staff-registered appointment is valid; the view saves the fields by hand.
# there is no "patient" field here - the view finds or creates the patient account itself,
# from the typed patient_name/patient_contact fields below
class StaffAppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        required=False,
    )

    class Meta:
        model = Appointment
        # fields checked by this form, in the order they appear on the dashboard add/edit page
        fields = [
            'department', 'date', 'time_slot', 'doctor', 'message', 'status',
            'patient_name', 'patient_contact', 'patient_age', 'patient_address', 'patient_nic',
        ]

    # stops a patient name that is just spaces from being saved
    def clean_patient_name(self):
        # pull the cleaned patient name value out of the form, with extra spaces removed
        patient_name = self.cleaned_data.get('patient_name', '').strip()
        # stop if nothing is left after removing spaces
        if not patient_name:
            raise forms.ValidationError("Please enter the patient's full name.")
        # name is fine
        return patient_name

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_patient_contact(self):
        # pull the cleaned phone value out of the form
        patient_contact = self.cleaned_data.get('patient_contact')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(patient_contact)
        # phone number is fine
        return patient_contact

    # stops an age that isn't realistic from being saved
    def clean_patient_age(self):
        # pull the cleaned age value out of the form
        patient_age = self.cleaned_data.get('patient_age')
        # stop if it is missing or zero/negative
        if patient_age is None or patient_age <= 0:
            raise forms.ValidationError("Please enter the patient's age.")
        # stop if it is unrealistically high
        if patient_age > 120:
            raise forms.ValidationError('Please enter a realistic age.')
        # age is fine
        return patient_age

    # stops an address that is just spaces from being saved
    def clean_patient_address(self):
        # pull the cleaned address value out of the form, with extra spaces removed
        patient_address = self.cleaned_data.get('patient_address', '').strip()
        # stop if nothing is left after removing spaces
        if not patient_address:
            raise forms.ValidationError("Please enter the patient's address.")
        # address is fine
        return patient_address

    # stops a NIC number that is not a valid Sri Lankan NIC shape from being saved
    def clean_patient_nic(self):
        # pull the cleaned NIC value out of the form, with extra spaces removed and letters capitalised
        patient_nic = self.cleaned_data.get('patient_nic', '').strip().upper()
        # raises an error if the NIC is not a sensible shape
        check_nic_number(patient_nic)
        # NIC is fine
        return patient_nic


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
