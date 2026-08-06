from django import forms  # django's form tools
from django.contrib.auth.models import User  # built-in user model (login, username, password)

# css class used on every input box, matches the login page style
fc = {'class': 'form-control form-control-user'}


class PatientSignupForm(forms.Form):
    """Fields for a visitor to create their own patient account. Only checks the data here - saving happens in the view."""
    # first name text box
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'First Name'}))
    # last name text box
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Last Name'}))
    # email text box
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Email Address'}))
    # username text box
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Username'}))
    # phone number text box, not required
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Phone Number (optional)'}))
    # password text box (hidden characters)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'}))
    # confirm password text box (hidden characters)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Confirm Password'}))

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
