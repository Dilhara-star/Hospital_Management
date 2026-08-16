# forms for supplier management
from django import forms  # import django's form tools
from .models import Supplier  # import our model


# form to check supplier data is valid; the view saves the fields by hand
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier  # this form is built from the supplier model
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'status']  # fields checked by this form
