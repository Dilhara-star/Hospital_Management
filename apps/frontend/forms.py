from datetime import date, timedelta  # used to check a date of birth is not in the future or unreasonably old
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password  # checks a password is strong enough
from apps.core.utils import check_phone_number, check_image_file  # checks a phone number and a picture file are sensible
from apps.user_management.models import UserProfile


class ProfileDetailsForm(forms.Form):
    """Fields checked when updating the logged in user's own details. Saving happens in the view."""
    first_name = forms.CharField(max_length=150, required=True)  # first name text box
    last_name = forms.CharField(max_length=150, required=True)  # last name text box
    email = forms.EmailField(required=True)  # email text box
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down

    # remembers which user is being edited, so clean_email can allow them to keep their own email
    def __init__(self, *args, user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own email
        self.user = user
        super().__init__(*args, **kwargs)

    # stops a first name that is just spaces from being saved
    def clean_first_name(self):
        # pull the cleaned first name value out of the form, with extra spaces removed
        first_name = self.cleaned_data.get('first_name', '').strip()
        # stop if nothing is left after removing spaces
        if not first_name:
            raise forms.ValidationError('Please enter your first name.')
        # first name is fine
        return first_name

    # stops a last name that is just spaces from being saved
    def clean_last_name(self):
        # pull the cleaned last name value out of the form, with extra spaces removed
        last_name = self.cleaned_data.get('last_name', '').strip()
        # stop if nothing is left after removing spaces
        if not last_name:
            raise forms.ValidationError('Please enter your last name.')
        # last name is fine
        return last_name

    # stops someone from switching their email to one another account already uses
    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # find any user that already has this email
        query = User.objects.filter(email=email)
        # do not count the user we are editing against themselves
        if self.user:
            query = query.exclude(pk=self.user.pk)
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

    # stops a date of birth being set in the future or an unreasonable number of years ago
    def clean_date_of_birth(self):
        # pull the cleaned date of birth value out of the form
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            # stop if the date is after today
            if dob > date.today():
                raise forms.ValidationError('Date of birth cannot be in the future.')
            # stop if the date is more than 120 years ago - not a realistic age
            earliest = date.today() - timedelta(days=120 * 365)
            if dob < earliest:
                raise forms.ValidationError('Please enter a valid date of birth.')
        # date is fine (or was left blank)
        return dob


class ProfilePictureForm(forms.Form):
    """Field checked when uploading a new profile picture. Saving happens in the view."""
    profile_picture = forms.ImageField(required=True)  # picture file upload

    # stops a picture file that is too big or the wrong type from being saved
    def clean_profile_picture(self):
        # pull the cleaned picture file out of the form
        profile_picture = self.cleaned_data.get('profile_picture')
        # raises an error if the file is too big or not an allowed image type
        check_image_file(profile_picture)
        # picture is fine
        return profile_picture


class ChangePasswordForm(forms.Form):
    """Fields checked when changing the logged in user's password. Saving happens in the view."""
    current_password = forms.CharField(widget=forms.PasswordInput)  # current password text box (hidden characters)
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

    # stops the password change if the two new password boxes don't match
    def clean(self):
        # run the normal checks first
        cleaned_data = super().clean()
        # get both new password values
        new = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        # show an error if they typed the passwords differently
        if new and confirm and new != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        # give back the checked data
        return cleaned_data

    # checks the typed "current password" actually matches the account's real password
    def validate_current_password(self, user):
        # true only if the typed current password matches the account's real password
        return user.check_password(self.cleaned_data.get('current_password', ''))
