# forms for supplier management
from django import forms  # import django's form tools
from apps.core.utils import check_phone_number  # checks a phone number is digits only, with a sensible length
from .models import Supplier  # import our model


# form to check supplier data is valid; the view saves the fields by hand
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier  # this form is built from the supplier model
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'status']  # fields checked by this form

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine (or was left blank)
        return phone
