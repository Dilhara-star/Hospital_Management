from django import forms
from django.contrib.auth.models import User
from apps.user_management.models import UserProfile


class ProfileDetailsForm(forms.Form):
    """Fields checked when updating the logged in user's own details. Saving happens in the view."""
    first_name = forms.CharField(max_length=150, required=False)  # first name text box
    last_name = forms.CharField(max_length=150, required=False)  # last name text box
    email = forms.EmailField(required=True)  # email text box
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    date_of_birth = forms.DateField(required=False)  # date of birth picker, not required
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False)  # gender drop-down

    # remembers which user is being edited, so clean_email can allow them to keep their own email
    def __init__(self, *args, user=None, **kwargs):
        # remember which user is being edited, so we can allow them to keep their own email
        self.user = user
        super().__init__(*args, **kwargs)

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


class ProfilePictureForm(forms.Form):
    """Field checked when uploading a new profile picture. Saving happens in the view."""
    profile_picture = forms.ImageField(required=True)  # picture file upload


class ChangePasswordForm(forms.Form):
    """Fields checked when changing the logged in user's password. Saving happens in the view."""
    current_password = forms.CharField(widget=forms.PasswordInput)  # current password text box (hidden characters)
    new_password = forms.CharField(widget=forms.PasswordInput)  # new password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # confirm new password text box (hidden characters)

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
