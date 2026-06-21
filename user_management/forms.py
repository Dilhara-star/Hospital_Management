# Django forms module එක import කරනවා
from django import forms
# Django built-in User model එක import කරනවා
from django.contrib.auth.models import User
# අපේ UserProfile model එක import කරනවා
from .models import UserProfile


# නව user කෙනෙක් හදන්න form class එක
class UserCreateForm(forms.Form):
    # user ගේ first name - අනිවාර්යයයි, උපරිම characters 150
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    # user ගේ last name - අනිවාර්යයයි, උපරිම characters 150
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    # user ගේ email address - අනිවාර්යයයි
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    # user ගේ username - අනිවාර්යයයි, උපරිම characters 150
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    # phone number - අනිවාර්ය නෑ, උපරිම characters 20
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    # උපන් දිනය - අනිවාර්ය නෑ, date picker widget එකක් use කරනවා
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    # gender - UserProfile ගේ GENDER_CHOICES use කරනවා, අනිවාර්ය නෑ
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    # role - UserProfile ගේ ROLE_CHOICES use කරනවා, අනිවාර්යයයි
    role = forms.ChoiceField(choices=[('', '---------')] + UserProfile.ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    # password - PasswordInput widget එකෙන් hide කරනවා
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    # password confirm කරන්න - PasswordInput widget එකෙන් hide කරනවා
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    # account active ද - default True
    is_active = forms.BooleanField(required=False, initial=True)

    # username unique ද කියලා check කරන clean method එක
    def clean_username(self):
        # validated username value එක ගන්නවා
        username = self.cleaned_data['username']
        # database එකේ same username කෙනෙක් ඉන්නවාද check කරනවා
        if User.objects.filter(username=username).exists():
            # ඉන්නවා නම් validation error එකක් දෙනවා
            raise forms.ValidationError('Username already exists.')
        # valid නම් username return කරනවා
        return username

    # email unique ද කියලා check කරන clean method එක
    def clean_email(self):
        # validated email value එක ගන්නවා
        email = self.cleaned_data['email']
        # database එකේ same email එකක් ඇද check කරනවා
        if User.objects.filter(email=email).exists():
            # ඇත්නම් validation error එකක් දෙනවා
            raise forms.ValidationError('Email address already in use.')
        # valid නම් email return කරනවා
        return email

    # සියලු fields එකවර validate කරන clean method එක
    def clean(self):
        # parent class ගේ clean method call කරලා cleaned data ගන්නවා
        cleaned_data = super().clean()
        # password value එක ගන්නවා
        password = cleaned_data.get('password')
        # confirm password value එක ගන්නවා
        confirm_password = cleaned_data.get('confirm_password')
        # දෙකම ඇත්නම් සහ match නොවෙනවා නම් error එකක් add කරනවා
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        # cleaned data return කරනවා
        return cleaned_data

    # User සහ UserProfile save කරන method එක
    def save(self):
        # validated form data ගන්නවා
        data = self.cleaned_data
        # Django User account එක create කරනවා
        user = User.objects.create_user(
            # username set කරනවා
            username=data['username'],
            # email set කරනවා
            email=data['email'],
            # password set කරනවා - Django automatically hash කරනවා
            password=data['password'],
            # first name set කරනවා
            first_name=data['first_name'],
            # last name set කරනවා
            last_name=data['last_name'],
            # account active status set කරනවා, නැත්නම් default True
            is_active=data.get('is_active', True),
        )
        # User account එකට link වෙන UserProfile create කරනවා
        UserProfile.objects.create(
            # User object එක link කරනවා
            user=user,
            # phone number set කරනවා, නැත්නම් empty string
            phone=data.get('phone', ''),
            # date of birth set කරනවා, නැත්නම් None
            date_of_birth=data.get('date_of_birth'),
            # gender set කරනවා, නැත්නම් empty string
            gender=data.get('gender', ''),
            # role set කරනවා
            role=data['role'],
        )
        # create කළ User object return කරනවා
        return user


# පවතින user කෙනෙක් edit කරන්න form class එක
class UserEditForm(forms.Form):
    # user ගේ first name - අනිවාර්යයයි, උපරිම characters 150
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    # user ගේ last name - අනිවාර්යයයි, උපරිම characters 150
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    # user ගේ email address - අනිවාර්යයයි
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    # user ගේ username - අනිවාර්යයයි, උපරිම characters 150
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    # phone number - අනිවාර්ය නෑ, උපරිම characters 20
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    # උපන් දිනය - අනිවාර්ය නෑ, date picker widget එකක් use කරනවා
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    # gender - UserProfile ගේ GENDER_CHOICES use කරනවා, අනිවාර්ය නෑ
    gender = forms.ChoiceField(choices=[('', '---------')] + UserProfile.GENDER_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    # role - UserProfile ගේ ROLE_CHOICES use කරනවා, අනිවාර්යයයි
    role = forms.ChoiceField(choices=[('', '---------')] + UserProfile.ROLE_CHOICES, required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    # account active ද - password field නෑ, edit කරනකොට password වෙනස් කරන්නේ නෑ
    is_active = forms.BooleanField(required=False)

    # instance (User object) accept කරලා initial data auto-populate කරන __init__
    def __init__(self, *args, instance=None, **kwargs):
        # instance එකෙන් initial data build කරනවා, ModelForm style
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

    # username unique ද කියලා check කරන clean method එක
    def clean_username(self):
        username = self.cleaned_data['username']
        qs = User.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Username already exists.')
        return username

    # email unique ද කියලා check කරන clean method එක
    def clean_email(self):
        email = self.cleaned_data['email']
        qs = User.objects.filter(email=email)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Email address already in use.')
        return email

    # User සහ UserProfile update කරන save method එක
    def save(self):
        data = self.cleaned_data
        user = self.instance
        # form data වලින් user fields update කරනවා
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.email = data['email']
        user.username = data['username']
        # active status update කරනවා, නැත්නම් default False
        user.is_active = data.get('is_active', False)
        # User object database එකේ save කරනවා
        user.save()

        # user ට link වෙච්ච profile object එක ගන්නවා
        profile = user.profile
        # form data වලින් profile fields update කරනවා
        profile.phone = data.get('phone', '')
        profile.date_of_birth = data.get('date_of_birth')
        profile.gender = data.get('gender', '')
        profile.role = data['role']
        # UserProfile object database එකේ save කරනවා
        profile.save()

        # updated User object return කරනවා
        return user
