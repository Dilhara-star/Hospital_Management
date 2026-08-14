from django import forms  # django's form tools
from django.contrib.auth.models import User  # built-in user model (login, username, password)


class PatientSignupForm(forms.Form):
    """Fields checked when a visitor creates their own patient account. Saving happens in the view."""
    first_name = forms.CharField(max_length=150, required=True)  # first name text box
    last_name = forms.CharField(max_length=150, required=True)  # last name text box
    email = forms.EmailField(required=True)  # email text box
    username = forms.CharField(max_length=150, required=True)  # username text box
    phone = forms.CharField(max_length=20, required=False)  # phone number text box, not required
    password = forms.CharField(widget=forms.PasswordInput)  # password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # confirm password text box (hidden characters)

    def clean_username(self):
        # pull the cleaned username value out of the form
        username = self.cleaned_data['username']
        # stop two accounts from sharing the same username
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        # username is free to use
        return username

    def clean_email(self):
        # pull the cleaned email value out of the form
        email = self.cleaned_data['email']
        # stop two accounts from sharing the same email address
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
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
