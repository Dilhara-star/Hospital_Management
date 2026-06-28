from django import forms
from django.contrib.auth.models import User
from apps.user_management.models import UserProfile


class ProfileDetailsForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    date_of_birth = forms.DateField(required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    gender = forms.ChoiceField(
        choices=[('', '---------')] + UserProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, user=None, **kwargs):
        if user is not None and 'initial' not in kwargs:
            profile = user.profile
            kwargs['initial'] = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': profile.phone,
                'date_of_birth': profile.date_of_birth,
                'gender': profile.gender,
            }
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    def save(self):
        data = self.cleaned_data
        user = self.user
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.save()
        profile = user.profile
        profile.phone = data.get('phone', '')
        profile.date_of_birth = data.get('date_of_birth')
        profile.gender = data.get('gender', '')
        profile.save()


class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField(required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}))

    def save(self, profile):
        profile.profile_picture = self.cleaned_data['profile_picture']
        profile.save()


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'}))
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}))
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))

    def clean(self):
        cleaned_data = super().clean()
        new = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if new and confirm and new != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def validate_current_password(self, user):
        return user.check_password(self.cleaned_data.get('current_password', ''))

    def save(self, user):
        user.set_password(self.cleaned_data['new_password'])
        user.save()
