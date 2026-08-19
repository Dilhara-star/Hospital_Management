from datetime import date  # used to check a date of birth is not in the future
from django import forms  # django's form tools
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.contrib.auth.validators import UnicodeUsernameValidator  # checks a username only has safe characters
from django.contrib.auth.password_validation import validate_password  # checks a password is strong enough
from apps.core.utils import check_phone_number  # checks a phone number is digits only, with a sensible length
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models

# role codes offered on the staff Role dropdown - lab technician is left out on purpose,
# so it can no longer be picked here (existing lab technician accounts still work fine)
STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist']


# ── Auth Forms ────────────────────────────────────────────────────────────────

class ForgotPasswordForm(forms.Form):
    """Field checked on the "forgot password" page. The lookup/email happens in the view."""
    email = forms.EmailField(required=True)  # email text box


class SetNewPasswordForm(forms.Form):
    """Fields checked when setting a new password from a reset link. Saving happens in the view."""
    new_password = forms.CharField(widget=forms.PasswordInput)  # new password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # confirm new password text box (hidden characters)

    # stops a weak new password (too short, too common, all numbers, ...) being used
    def clean_new_password(self):
        # pull the cleaned new password value out of the form
        new_password = self.cleaned_data.get('new_password')
        # runs the password rules set in settings.py; raises an error if the password is too weak
        validate_password(new_password)
        # password is strong enough
        return new_password

    # stops the reset if the two new password boxes don't match
    def clean(self):
        # run the normal checks first
        cleaned_data = super().clean()
        # get both new password values
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        # show an error if they typed the passwords differently
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        # give back the checked data
        return cleaned_data


# ── Patient Forms ─────────────────────────────────────────────────────────────

class PatientCreateForm(forms.Form):
    """Fields checked when registering a brand new patient. Saving happens in the view."""
    # Account
    first_name = forms.CharField(max_length=150)  # first name text box
    last_name = forms.CharField(max_length=150)  # last name text box
    email = forms.EmailField()  # email text box
    username = forms.CharField(max_length=150)  # username text box
    password = forms.CharField(widget=forms.PasswordInput)  # password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # confirm password text box (hidden characters)
    is_active = forms.BooleanField(required=False, initial=True)  # checkbox for whether the account can log in
    # Personal
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down
    address = forms.CharField(required=False, widget=forms.Textarea)  # home address multi-line box, not required
    # Medical
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False)  # blood type drop-down
    allergies = forms.CharField(required=False, widget=forms.Textarea)  # known allergies multi-line box, not required
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea)  # chronic conditions multi-line box, not required
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False)  # emergency contact name text box
    emergency_contact_phone = forms.CharField(max_length=20, required=False)  # emergency contact phone text box
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False)  # relationship drop-down
    # Insurance
    insurance_provider = forms.CharField(max_length=100, required=False)  # insurance provider name text box
    insurance_number = forms.CharField(max_length=50, required=False)  # insurance policy number text box
    insurance_expiry = forms.DateField(required=False)  # insurance expiry date picker, not required
    # Status
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES)  # patient status drop-down (active, inactive, discharged)

    # stops two patients from sharing the same username
    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if it has characters other than letters, numbers, and @/./+/-/_
        UnicodeUsernameValidator()(username)
        # stop if another user already has this username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    # stops two patients from sharing the same email address
    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # stop if another user already has this email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

    # stops a weak password (too short, too common, all numbers, ...) being used
    def clean_password(self):
        # pull the cleaned password value out of the form
        password = self.cleaned_data.get('password')
        # runs the password rules set in settings.py; raises an error if the password is too weak
        validate_password(password)
        # password is strong enough
        return password

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops an emergency contact phone number that is not digits (or a sensible length) from being saved
    def clean_emergency_contact_phone(self):
        # pull the cleaned emergency contact phone value out of the form
        phone = self.cleaned_data.get('emergency_contact_phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops a date of birth being set in the future
    def clean_date_of_birth(self):
        # pull the cleaned date of birth value out of the form
        dob = self.cleaned_data.get('date_of_birth')
        # stop if a date was picked and it is after today
        if dob and dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        # date is fine (or was left blank)
        return dob

    # stops an insurance policy expiry date being set in the past
    def clean_insurance_expiry(self):
        # pull the cleaned insurance expiry value out of the form
        expiry = self.cleaned_data.get('insurance_expiry')
        # stop if a date was picked and it is before today
        if expiry and expiry < date.today():
            raise forms.ValidationError('Insurance expiry date cannot be in the past.')
        # date is fine (or was left blank)
        return expiry

    # stops registration if the two password boxes don't match
    def clean(self):
        # run the normal checks first
        cleaned_data = super().clean()
        # get both password values
        pw = cleaned_data.get('password')
        cpw = cleaned_data.get('confirm_password')
        # show an error if they typed the passwords differently
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        # give back the checked data
        return cleaned_data


class PatientEditForm(forms.Form):
    """Fields checked when editing an existing patient. Saving happens in the view."""
    # Account
    first_name = forms.CharField(max_length=150)  # first name text box
    last_name = forms.CharField(max_length=150)  # last name text box
    email = forms.EmailField()  # email text box
    username = forms.CharField(max_length=150)  # username text box
    is_active = forms.BooleanField(required=False)  # checkbox for whether the account can log in
    # Personal
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down
    address = forms.CharField(required=False, widget=forms.Textarea)  # home address multi-line box, not required
    # Medical
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False)  # blood type drop-down
    allergies = forms.CharField(required=False, widget=forms.Textarea)  # known allergies multi-line box, not required
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea)  # chronic conditions multi-line box, not required
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False)  # emergency contact name text box
    emergency_contact_phone = forms.CharField(max_length=20, required=False)  # emergency contact phone text box
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False)  # relationship drop-down
    # Insurance
    insurance_provider = forms.CharField(max_length=100, required=False)  # insurance provider name text box
    insurance_number = forms.CharField(max_length=50, required=False)  # insurance policy number text box
    insurance_expiry = forms.DateField(required=False)  # insurance expiry date picker, not required
    # Status
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES)  # patient status drop-down (active, inactive, discharged)

    # remembers which patient is being edited, so clean_username/clean_email can allow them to keep their own values
    def __init__(self, *args, current_user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own username/email
        self.current_user = current_user
        # run the normal form setup
        super().__init__(*args, **kwargs)

    # stops this patient from switching to a username another account already uses
    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if it has characters other than letters, numbers, and @/./+/-/_
        UnicodeUsernameValidator()(username)
        # find any user that already has this username
        query = User.objects.filter(username=username)
        # do not count the user we are editing against themselves
        if self.current_user:
            query = query.exclude(pk=self.current_user.pk)
        # stop if someone else already has this username
        if query.exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    # stops this patient from switching to an email another account already uses
    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # find any user that already has this email
        query = User.objects.filter(email=email)
        # do not count the user we are editing against themselves
        if self.current_user:
            query = query.exclude(pk=self.current_user.pk)
        # stop if someone else already has this email
        if query.exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops an emergency contact phone number that is not digits (or a sensible length) from being saved
    def clean_emergency_contact_phone(self):
        # pull the cleaned emergency contact phone value out of the form
        phone = self.cleaned_data.get('emergency_contact_phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops a date of birth being set in the future
    def clean_date_of_birth(self):
        # pull the cleaned date of birth value out of the form
        dob = self.cleaned_data.get('date_of_birth')
        # stop if a date was picked and it is after today
        if dob and dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        # date is fine (or was left blank)
        return dob

    # stops an insurance policy expiry date being set in the past
    def clean_insurance_expiry(self):
        # pull the cleaned insurance expiry value out of the form
        expiry = self.cleaned_data.get('insurance_expiry')
        # stop if a date was picked and it is before today
        if expiry and expiry < date.today():
            raise forms.ValidationError('Insurance expiry date cannot be in the past.')
        # date is fine (or was left blank)
        return expiry


# ── Staff Forms ───────────────────────────────────────────────────────────────

# drop-down choices for staff roles only (skips "patient" and plain "user")
STAFF_ROLE_CHOICES = [('', '---------')]
# go through every role choice one by one
for role_code, role_label in UserProfile.ROLE_CHOICES:
    # keep it only if it is a staff role
    if role_code in STAFF_ROLES:
        STAFF_ROLE_CHOICES.append((role_code, role_label))


class StaffCreateForm(forms.Form):
    """Fields checked when adding a brand new staff member. Saving happens in the view."""
    first_name = forms.CharField(max_length=150, required=True)  # first name text box
    last_name = forms.CharField(max_length=150, required=True)  # last name text box
    email = forms.EmailField(required=True)  # email text box
    username = forms.CharField(max_length=150, required=True)  # username text box
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, required=True)  # staff role drop-down, required
    password = forms.CharField(widget=forms.PasswordInput)  # password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # confirm password text box (hidden characters)
    is_active = forms.BooleanField(required=False, initial=True)  # checkbox for whether the account can log in

    # stops two staff members from sharing the same username
    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if it has characters other than letters, numbers, and @/./+/-/_
        UnicodeUsernameValidator()(username)
        # stop if another user already has this username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    # stops two staff members from sharing the same email address
    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # stop if another user already has this email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

    # stops a weak password (too short, too common, all numbers, ...) being used
    def clean_password(self):
        # pull the cleaned password value out of the form
        password = self.cleaned_data.get('password')
        # runs the password rules set in settings.py; raises an error if the password is too weak
        validate_password(password)
        # password is strong enough
        return password

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops a date of birth being set in the future
    def clean_date_of_birth(self):
        # pull the cleaned date of birth value out of the form
        dob = self.cleaned_data.get('date_of_birth')
        # stop if a date was picked and it is after today
        if dob and dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        # date is fine (or was left blank)
        return dob

    # stops registration if the two password boxes don't match
    def clean(self):
        # run the normal checks first
        cleaned_data = super().clean()
        # get both password values
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        # show an error if they typed the passwords differently
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        # give back the checked data
        return cleaned_data


class StaffEditForm(forms.Form):
    """Fields checked when editing an existing staff member. Saving happens in the view."""
    # Account
    first_name = forms.CharField(max_length=150)  # first name text box
    last_name = forms.CharField(max_length=150)  # last name text box
    email = forms.EmailField()  # email text box
    username = forms.CharField(max_length=150)  # username text box
    is_active = forms.BooleanField(required=False)  # checkbox for whether the account can log in
    # Personal
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, required=True)  # staff role drop-down, required
    # Employment
    department = forms.ChoiceField(choices=StaffProfile.DEPARTMENT_CHOICES, required=False)  # department drop-down
    specialization = forms.CharField(max_length=100, required=False)  # specialization text box, not required
    qualification = forms.CharField(max_length=100, required=False)  # qualification text box, not required
    license_number = forms.CharField(max_length=50, required=False)  # license number text box, not required
    hire_date = forms.DateField(required=False)  # hire date picker, not required
    employment_type = forms.ChoiceField(choices=StaffProfile.EMPLOYMENT_TYPE_CHOICES, required=False)  # employment type drop-down
    shift = forms.ChoiceField(choices=StaffProfile.SHIFT_CHOICES, required=False)  # shift drop-down
    hourly_fee = forms.DecimalField(required=False, min_value=0)  # doctor's own consultation fee (doctors only)
    years_of_experience = forms.IntegerField(required=False, min_value=0)  # doctor's years of practice (doctors only)
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False)  # emergency contact name text box
    emergency_contact_phone = forms.CharField(max_length=20, required=False)  # emergency contact phone text box

    # remembers which staff member is being edited, so clean_username/clean_email can allow them to keep their own values
    def __init__(self, *args, current_user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own username/email
        self.current_user = current_user
        # run the normal form setup
        super().__init__(*args, **kwargs)

    # stops this staff member from switching to a username another account already uses
    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if it has characters other than letters, numbers, and @/./+/-/_
        UnicodeUsernameValidator()(username)
        # find any user that already has this username
        query = User.objects.filter(username=username)
        # do not count the user we are editing against themselves
        if self.current_user:
            query = query.exclude(pk=self.current_user.pk)
        # stop if someone else already has this username
        if query.exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    # stops this staff member from switching to an email another account already uses
    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # find any user that already has this email
        query = User.objects.filter(email=email)
        # do not count the user we are editing against themselves
        if self.current_user:
            query = query.exclude(pk=self.current_user.pk)
        # stop if someone else already has this email
        if query.exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops an emergency contact phone number that is not digits (or a sensible length) from being saved
    def clean_emergency_contact_phone(self):
        # pull the cleaned emergency contact phone value out of the form
        phone = self.cleaned_data.get('emergency_contact_phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone

    # stops a date of birth being set in the future
    def clean_date_of_birth(self):
        # pull the cleaned date of birth value out of the form
        dob = self.cleaned_data.get('date_of_birth')
        # stop if a date was picked and it is after today
        if dob and dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        # date is fine (or was left blank)
        return dob

    # stops a hire date being set in the future
    def clean_hire_date(self):
        # pull the cleaned hire date value out of the form
        hire_date = self.cleaned_data.get('hire_date')
        # stop if a date was picked and it is after today
        if hire_date and hire_date > date.today():
            raise forms.ValidationError('Hire date cannot be in the future.')
        # date is fine (or was left blank)
        return hire_date
