# forms for supplier management
from django import forms  # import django's form tools
from apps.core.utils import check_phone_number  # checks a phone number is digits only, with a sensible length
from .models import Supplier  # import our model


# form to check supplier data is valid; the view saves the fields by hand
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier  # this form is built from the supplier model
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'status']  # fields checked by this form

    # the model itself allows phone/email/address to be blank, but a supplier is not
    # usable without a way to contact them, so this form makes those three required
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = True
        self.fields['email'].required = True
        self.fields['address'].required = True

    # stops a supplier name that is just spaces, or already used by another supplier
    def clean_name(self):
        # pull the cleaned name value out of the form, with extra spaces removed
        name = self.cleaned_data.get('name', '').strip()
        # stop if nothing is left after removing spaces
        if not name:
            raise forms.ValidationError('Please enter a supplier name.')
        # find any other supplier that already has this name
        query = Supplier.objects.filter(name__iexact=name)
        # do not count the supplier we are editing against itself
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        # stop if another supplier already has this name
        if query.exists():
            raise forms.ValidationError('A supplier with this name already exists.')
        # name is fine
        return name

    # stops a phone number that is not digits (or a sensible length) from being saved
    def clean_phone(self):
        # pull the cleaned phone value out of the form
        phone = self.cleaned_data.get('phone')
        # raises an error if the phone number is not a sensible shape
        check_phone_number(phone)
        # phone number is fine
        return phone

    # stops an address that is just spaces from being saved
    def clean_address(self):
        # pull the cleaned address value out of the form, with extra spaces removed
        address = self.cleaned_data.get('address', '').strip()
        # stop if nothing is left after removing spaces
        if not address:
            raise forms.ValidationError('Please enter a supplier address.')
        # address is fine
        return address
