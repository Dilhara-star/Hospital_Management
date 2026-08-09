from django import forms  # django's form tools
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models

# role codes that count as "staff" (not a patient, not a plain "user")
STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']

# css class used on every text/number/date input box
fc = {'class': 'form-control'}
# css class + html type used on date input boxes
fc_date = {'class': 'form-control', 'type': 'date'}
# css class used on multi-line text boxes, 3 rows tall
fc_ta = {'class': 'form-control', 'rows': '3'}


# ── Patient Forms ─────────────────────────────────────────────────────────────

class PatientCreateForm(forms.Form):
    """Fields for registering a brand new patient. Saving happens in the view."""
    # Account
    # first name text box
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # last name text box
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # email text box
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    # username text box
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # password text box (hidden characters)
    password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    # confirm password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    # checkbox for whether the account can log in, ticked by default
    is_active = forms.BooleanField(required=False, initial=True)
    # Personal
    # phone number text box, not required
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # date of birth picker, not required
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # gender drop-down, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # home address multi-line box, not required
    address = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Medical
    # blood type drop-down, not required
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # known allergies multi-line box, not required
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # chronic conditions multi-line box, not required
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Emergency contact
    # emergency contact name text box, not required
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # emergency contact phone text box, not required
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # emergency contact relationship drop-down, not required
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # Insurance
    # insurance provider name text box, not required
    insurance_provider = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # insurance policy number text box, not required
    insurance_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    # insurance expiry date picker, not required
    insurance_expiry = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # Status
    # patient status drop-down (active, inactive, discharged)
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES, widget=forms.Select(attrs=fc))

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
    """Fields for editing an existing patient. Saving happens in the view."""
    # Account
    # first name text box
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # last name text box
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # email text box
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    # username text box
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # checkbox for whether the account can log in
    is_active = forms.BooleanField(required=False)
    # Personal
    # phone number text box, not required
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # date of birth picker, not required
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # gender drop-down, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # home address multi-line box, not required
    address = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Medical
    # blood type drop-down, not required
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # known allergies multi-line box, not required
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # chronic conditions multi-line box, not required
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Emergency contact
    # emergency contact name text box, not required
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # emergency contact phone text box, not required
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # emergency contact relationship drop-down, not required
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # Insurance
    # insurance provider name text box, not required
    insurance_provider = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # insurance policy number text box, not required
    insurance_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    # insurance expiry date picker, not required
    insurance_expiry = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # Status
    # patient status drop-down (active, inactive, discharged)
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES, widget=forms.Select(attrs=fc))

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
    """Fields for adding a brand new staff member. Saving happens in the view."""
    # first name text box
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    # last name text box
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    # email text box
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=fc))
    # username text box
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    # phone number text box, not required
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # date of birth picker, not required
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # gender drop-down, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # staff role drop-down, required (admin, doctor, nurse, receptionist, pharmacist, lab technician)
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, required=True, widget=forms.Select(attrs=fc))
    # password text box (hidden characters)
    password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    # confirm password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    # checkbox for whether the account can log in, ticked by default
    is_active = forms.BooleanField(required=False, initial=True)

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
    """Fields for editing an existing staff member. Saving happens in the view."""
    # Account
    # first name text box
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # last name text box
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # email text box
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    # username text box
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    # checkbox for whether the account can log in
    is_active = forms.BooleanField(required=False)
    # Personal
    # phone number text box, not required
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    # date of birth picker, not required
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # gender drop-down, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # staff role drop-down, required
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, required=True, widget=forms.Select(attrs=fc))
    # Employment
    # department drop-down, not required
    department = forms.ChoiceField(choices=StaffProfile.DEPARTMENT_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # specialization text box, not required
    specialization = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # qualification text box, not required
    qualification = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # license number text box, not required
    license_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    # hire date picker, not required
    hire_date = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # employment type drop-down, not required
    employment_type = forms.ChoiceField(choices=StaffProfile.EMPLOYMENT_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # shift drop-down, not required
    shift = forms.ChoiceField(choices=StaffProfile.SHIFT_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # doctor's own consultation fee, added on top of the department fee (doctors only)
    hourly_fee = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}))
    # Emergency contact
    # emergency contact name text box, not required
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    # emergency contact phone text box, not required
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))

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
