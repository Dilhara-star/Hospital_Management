from django import forms
from django.contrib.auth.models import User
from apps.user_management.models import UserProfile, PatientProfile

# shared css classes, so the sign up form matches the login page style
fc = {'class': 'form-control form-control-user'}


class SignupForm(forms.Form):
    # this form lets a visitor create their own patient account
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={**fc, 'placeholder': 'Email Address'}))
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Username'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={**fc, 'placeholder': 'Phone Number (optional)'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={**fc, 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={**fc, 'placeholder': 'Confirm Password'}))

    def clean_username(self):
        # stop two accounts from sharing the same username
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        # stop two accounts from sharing the same email address
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        # make sure the user typed the same password twice
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self):
        # create the User, then its patient profiles, and return the new user
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        UserProfile.objects.create(user=user, phone=data.get('phone', ''), role='patient')
        PatientProfile.objects.create(user=user)
        return user
