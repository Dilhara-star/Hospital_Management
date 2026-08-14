from django import forms  # django's form tools
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models

# role codes that count as "staff" (not a patient, not a plain "user")
STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']


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

    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if another user already has this username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # stop if another user already has this email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

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

    def __init__(self, *args, current_user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own username/email
        self.current_user = current_user
        # run the normal form setup
        super().__init__(*args, **kwargs)

    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
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

    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop if another user already has this username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        # username is free to use
        return username

    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # stop if another user already has this email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        # email is free to use
        return email

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
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False)  # emergency contact name text box
    emergency_contact_phone = forms.CharField(max_length=20, required=False)  # emergency contact phone text box

    def __init__(self, *args, current_user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own username/email
        self.current_user = current_user
        # run the normal form setup
        super().__init__(*args, **kwargs)

    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
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
