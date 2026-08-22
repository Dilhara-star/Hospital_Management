import re
from datetime import date

from django import forms
from django.contrib.auth.models import User

from apps.core.utils import check_phone_number, check_nic_number  # checks a phone number and a NIC number are sensible
from .models import Appointment, Payment


# form to check a patient's own booking is valid; the view saves the fields by hand
# me Frontend Appoiment.
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
        # stops a blank or too short name, and blocks numbers/symbols in the name
    def clean_patient_name(self):
        name = self.cleaned_data['patient_name'].strip()  # remove extra spaces from the start/end
        if len(name) < 2:  # a real name needs at least 2 letters
            raise forms.ValidationError("Please enter the patient's full name.")
        for char in name:  # check every character in the name one by one
            if not (char.isalpha() or char in " .'-"):  # only letters, spaces, dots, apostrophes, hyphens allowed
                raise forms.ValidationError("Name can only contain letters, spaces, and . ' -")
        return name
    
        # stops a contact number that is not a valid 10 digit Sri Lankan number
    def clean_patient_contact(self):
        contact = self.cleaned_data['patient_contact'].strip()  # remove extra spaces
        contact = contact.replace(' ', '').replace('-', '')  # remove spaces/dashes typed inside the number
        if not contact.isdigit() or len(contact) != 10 or not contact.startswith('0'):  # e.g. 0771234567
            raise forms.ValidationError('Enter a valid 10 digit contact number, e.g. 0771234567.')
        return contact

        # stops an age that is not realistic for a patient
    def clean_patient_age(self):
        age = self.cleaned_data['patient_age']  # age typed on the form
        if age < 1 or age > 120:  # a real patient's age is always in this range
            raise forms.ValidationError('Enter a valid age between 1 and 120.')
        return age

        # stops a blank or too short address
    def clean_patient_address(self):
        address = self.cleaned_data['patient_address'].strip()  # remove extra spaces
        if len(address) < 5:  # a real address is always longer than this
            raise forms.ValidationError('Please enter a valid address.')
        return address
    
        # stops a NIC number that does not match the Sri Lankan NIC format
    def clean_patient_nic(self):
        nic = self.cleaned_data['patient_nic'].strip().upper()  # remove spaces, make the V/X letter uppercase
        old_format = re.match(r'^\d{9}[VX]$', nic)  # old NIC: 9 digits then V or X, e.g. 991234567V
        new_format = re.match(r'^\d{12}$', nic)  # new NIC: 12 digits, e.g. 199912345678
        if not old_format and not new_format:
            raise forms.ValidationError('Enter a valid NIC number, e.g. 991234567V or 199912345678.')
        return nic


# form to check a staff-registered appointment is valid; the view saves the fields by hand.
# there is no "patient" field here - the view finds or creates the patient account itself,
# from the typed patient_name/patient_contact fields below
# meka dashboard eke appointment add/edit page ekata form ekak
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

    # stops a blank or too short name, and blocks numbers/symbols in the name
    def clean_patient_name(self):
        name = self.cleaned_data['patient_name'].strip()  # remove extra spaces from the start/end
        if len(name) < 2:  # a real name needs at least 2 letters
            raise forms.ValidationError("Please enter the patient's full name.")
        for char in name:  # check every character in the name one by one
            if not (char.isalpha() or char in " .'-"):  # only letters, spaces, dots, apostrophes, hyphens allowed
                raise forms.ValidationError("Name can only contain letters, spaces, and . ' -")
        return name

    # stops a contact number that is not a valid 10 digit Sri Lankan number
    def clean_patient_contact(self):
        contact = self.cleaned_data['patient_contact'].strip()  # remove extra spaces
        contact = contact.replace(' ', '').replace('-', '')  # remove spaces/dashes typed inside the number
        if not contact.isdigit() or len(contact) != 10 or not contact.startswith('0'):  # e.g. 0771234567
            raise forms.ValidationError('Enter a valid 10 digit contact number, e.g. 0771234567.')
        return contact

    def clean_date(self):
        # stop the patient from rescheduling into the past
        new_date = self.cleaned_data['date']
        if new_date < date.today():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return new_date

    # stops an age that is not realistic for a patient
    def clean_patient_age(self):
        age = self.cleaned_data['patient_age']  # age typed on the form
        if age < 1 or age > 120:  # a real patient's age is always in this range
            raise forms.ValidationError('Enter a valid age between 1 and 120.')
        return age

    # stops a blank or too short address
    def clean_patient_address(self):
        address = self.cleaned_data['patient_address'].strip()  # remove extra spaces
        if len(address) < 5:  # a real address is always longer than this
            raise forms.ValidationError('Please enter a valid address.')
        return address

    def clean_patient_nic(self):
        nic = self.cleaned_data['patient_nic'].strip().upper()  # remove spaces, make the V/X letter uppercase
        old_format = re.match(r'^\d{9}[VX]$', nic)  # old NIC: 9 digits then V or X, e.g. 991234567V
        new_format = re.match(r'^\d{12}$', nic)  # new NIC: 12 digits, e.g. 199912345678
        if not old_format and not new_format:
            raise forms.ValidationError('Enter a valid NIC number, e.g. 991234567V or 199912345678.')
        return nic
    
    # stops staff booking a doctor who is already booked for that date and time slot
    def clean(self):
        cleaned_data = super().clean()  # run the normal field checks first
        appointment_date = cleaned_data.get('date')  # date picked on the form
        time_slot = cleaned_data.get('time_slot')  # time slot picked on the form
        doctor = cleaned_data.get('doctor')  # doctor picked on the form; read from cleaned_data so this
        # also catches a doctor change on the edit page, not just the old doctor stored on the instance
        if doctor and appointment_date and time_slot:  # only checkable once all three are known
            clash = Appointment.objects.filter(
                doctor=doctor, date=appointment_date, time_slot=time_slot,
            ).exclude(status='cancelled').exclude(pk=self.instance.pk)  # a cancelled slot is free, and skip itself
            if clash.exists():  # someone else already has this doctor booked at this time
                self.add_error('time_slot', 'This doctor is already booked for that date and time slot. Please pick another slot.')
        return cleaned_data


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

    