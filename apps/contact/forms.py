# form to check a "Contact Us" message is valid; the view saves it by hand
from django import forms
from .models import Contact_us


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact_us  # this form is built from the contact message model
        fields = ['name', 'email', 'subject', 'message']  # fields checked by this form
