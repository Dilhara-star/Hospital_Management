from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, PatientProfile, StaffProfile


STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']

fc = {'class': 'form-control'}
fc_date = {'class': 'form-control', 'type': 'date'}
fc_ta = {'class': 'form-control', 'rows': '3'}


class UserCreateForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={**fc, 'placeholder': 'Email Address'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Username'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Phone Number'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    role = forms.ChoiceField(choices=[('', '---------')] + UserProfile.ROLE_CHOICES, required=True, widget=forms.Select(attrs=fc))
    password = forms.CharField(widget=forms.PasswordInput(attrs={**fc, 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={**fc, 'placeholder': 'Confirm Password'}))
    is_active = forms.BooleanField(required=False, initial=True)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_active=data.get('is_active', True),
        )
        UserProfile.objects.create(
            user=user,
            phone=data.get('phone', ''),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender', ''),
            role=data['role'],
        )
        return user


class UserEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=fc))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs=fc))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    role = forms.ChoiceField(choices=[('', '---------')] + UserProfile.ROLE_CHOICES, required=True, widget=forms.Select(attrs=fc))
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, instance=None, **kwargs):
        if instance is not None and 'initial' not in kwargs:
            profile = instance.profile
            kwargs['initial'] = {
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'email': instance.email,
                'username': instance.username,
                'is_active': instance.is_active,
                'phone': profile.phone,
                'date_of_birth': profile.date_of_birth,
                'gender': profile.gender,
                'role': profile.role,
            }
        super().__init__(*args, **kwargs)
        self.instance = instance

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def save(self):
        data = self.cleaned_data
        user = self.instance
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.username = data['username']
        user.is_active = data.get('is_active', False)
        user.save()
        profile = user.profile
        profile.phone = data.get('phone', '')
        profile.date_of_birth = data.get('date_of_birth')
        profile.gender = data.get('gender', '')
        profile.role = data['role']
        profile.save()
        return user


# ── Patient Forms ─────────────────────────────────────────────────────────────

class PatientCreateForm(forms.Form):
    # Account
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs=fc))
    is_active = forms.BooleanField(required=False, initial=True)
    # Personal
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Medical
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # Insurance
    insurance_provider = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    insurance_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    insurance_expiry = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # Status
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES, widget=forms.Select(attrs=fc))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        cpw = cleaned_data.get('confirm_password')
        if pw and cpw and pw != cpw:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_active=data.get('is_active', True),
        )
        UserProfile.objects.create(
            user=user,
            phone=data.get('phone', ''),
            date_of_birth=data.get('date_of_birth'),
            gender=data.get('gender', ''),
            role='patient',
        )
        patient = PatientProfile.objects.create(
            user=user,
            blood_type=data.get('blood_type', ''),
            allergies=data.get('allergies', ''),
            chronic_conditions=data.get('chronic_conditions', ''),
            address=data.get('address', ''),
            emergency_contact_name=data.get('emergency_contact_name', ''),
            emergency_contact_phone=data.get('emergency_contact_phone', ''),
            emergency_contact_relationship=data.get('emergency_contact_relationship', ''),
            insurance_provider=data.get('insurance_provider', ''),
            insurance_number=data.get('insurance_number', ''),
            insurance_expiry=data.get('insurance_expiry'),
            status=data.get('status', 'active'),
        )
        return patient


class PatientEditForm(forms.Form):
    # Account
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    is_active = forms.BooleanField(required=False)
    # Personal
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Medical
    blood_type = forms.ChoiceField(choices=PatientProfile.BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs=fc_ta))
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    emergency_contact_relationship = forms.ChoiceField(choices=PatientProfile.RELATIONSHIP_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # Insurance
    insurance_provider = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    insurance_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    insurance_expiry = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    # Status
    status = forms.ChoiceField(choices=PatientProfile.STATUS_CHOICES, widget=forms.Select(attrs=fc))

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        if instance and 'initial' not in kwargs:
            user = instance.user
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = None
            kwargs['initial'] = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'username': user.username,
                'is_active': user.is_active,
                'phone': profile.phone if profile else '',
                'date_of_birth': profile.date_of_birth if profile else None,
                'gender': profile.gender if profile else '',
                'address': instance.address,
                'blood_type': instance.blood_type,
                'allergies': instance.allergies,
                'chronic_conditions': instance.chronic_conditions,
                'emergency_contact_name': instance.emergency_contact_name,
                'emergency_contact_phone': instance.emergency_contact_phone,
                'emergency_contact_relationship': instance.emergency_contact_relationship,
                'insurance_provider': instance.insurance_provider,
                'insurance_number': instance.insurance_number,
                'insurance_expiry': instance.insurance_expiry,
                'status': instance.status,
            }
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def save(self):
        data = self.cleaned_data
        patient = self.instance
        user = patient.user

        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.username = data['username']
        user.is_active = data.get('is_active', False)
        user.save()

        profile = user.profile
        profile.phone = data.get('phone', '')
        profile.date_of_birth = data.get('date_of_birth')
        profile.gender = data.get('gender', '')
        profile.save()

        patient.blood_type = data.get('blood_type', '')
        patient.allergies = data.get('allergies', '')
        patient.chronic_conditions = data.get('chronic_conditions', '')
        patient.address = data.get('address', '')
        patient.emergency_contact_name = data.get('emergency_contact_name', '')
        patient.emergency_contact_phone = data.get('emergency_contact_phone', '')
        patient.emergency_contact_relationship = data.get('emergency_contact_relationship', '')
        patient.insurance_provider = data.get('insurance_provider', '')
        patient.insurance_number = data.get('insurance_number', '')
        patient.insurance_expiry = data.get('insurance_expiry')
        patient.status = data.get('status', 'active')
        patient.save()

        return patient


# ── Staff Forms ───────────────────────────────────────────────────────────────

STAFF_ROLE_CHOICES = [('', '---------')] + [
    (k, v) for k, v in UserProfile.ROLE_CHOICES if k in STAFF_ROLES
]


class StaffEditForm(forms.Form):
    # Account
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    email = forms.EmailField(widget=forms.EmailInput(attrs=fc))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs=fc))
    is_active = forms.BooleanField(required=False)
    # Personal
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs=fc))
    role = forms.ChoiceField(choices=STAFF_ROLE_CHOICES, required=True, widget=forms.Select(attrs=fc))
    # Employment
    department = forms.ChoiceField(choices=StaffProfile.DEPARTMENT_CHOICES, required=False, widget=forms.Select(attrs=fc))
    specialization = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    qualification = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    license_number = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs=fc))
    hire_date = forms.DateField(required=False, widget=forms.DateInput(attrs=fc_date))
    employment_type = forms.ChoiceField(choices=StaffProfile.EMPLOYMENT_TYPE_CHOICES, required=False, widget=forms.Select(attrs=fc))
    shift = forms.ChoiceField(choices=StaffProfile.SHIFT_CHOICES, required=False, widget=forms.Select(attrs=fc))
    # Emergency contact
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs=fc))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=fc))

    def __init__(self, *args, user_instance=None, **kwargs):
        self.user_instance = user_instance
        if user_instance and 'initial' not in kwargs:
            profile = user_instance.profile
            try:
                sp = profile.staff_profile
            except StaffProfile.DoesNotExist:
                sp = None
            initial = {
                'first_name': user_instance.first_name,
                'last_name': user_instance.last_name,
                'email': user_instance.email,
                'username': user_instance.username,
                'is_active': user_instance.is_active,
                'phone': profile.phone,
                'date_of_birth': profile.date_of_birth,
                'gender': profile.gender,
                'role': profile.role,
            }
            if sp:
                initial.update({
                    'department': sp.department,
                    'specialization': sp.specialization,
                    'qualification': sp.qualification,
                    'license_number': sp.license_number,
                    'hire_date': sp.hire_date,
                    'employment_type': sp.employment_type,
                    'shift': sp.shift,
                    'emergency_contact_name': sp.emergency_contact_name,
                    'emergency_contact_phone': sp.emergency_contact_phone,
                })
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.user_instance:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.user_instance:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def save(self):
        data = self.cleaned_data
        user = self.user_instance

        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.username = data['username']
        user.is_active = data.get('is_active', False)
        user.save()

        profile = user.profile
        profile.phone = data.get('phone', '')
        profile.date_of_birth = data.get('date_of_birth')
        profile.gender = data.get('gender', '')
        profile.role = data['role']
        profile.save()

        sp, _ = StaffProfile.objects.get_or_create(user_profile=profile)
        sp.department = data.get('department', '')
        sp.specialization = data.get('specialization', '')
        sp.qualification = data.get('qualification', '')
        sp.license_number = data.get('license_number', '')
        sp.hire_date = data.get('hire_date')
        sp.employment_type = data.get('employment_type', '')
        sp.shift = data.get('shift', '')
        sp.emergency_contact_name = data.get('emergency_contact_name', '')
        sp.emergency_contact_phone = data.get('emergency_contact_phone', '')
        sp.save()

        return user
