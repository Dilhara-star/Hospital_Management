# forms for supplier and medicine inventory management
from django import forms  # import django's form tools
from .models import Supplier, Medicine, MedicineStock  # import our models

# shared widget attributes, so every input looks the same (bootstrap style)
fc = {'class': 'form-control'}  # plain text/number/select input
fc_date = {'class': 'form-control', 'type': 'date'}  # date picker input
fc_ta = {'class': 'form-control', 'rows': '3'}  # textarea input


# form to add or edit a supplier
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier  # this form is built from the supplier model
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'status']  # fields shown on the form
        widgets = {
            'name': forms.TextInput(attrs=fc),  # supplier name input
            'contact_person': forms.TextInput(attrs=fc),  # contact person input
            'phone': forms.TextInput(attrs=fc),  # phone number input
            'email': forms.EmailInput(attrs=fc),  # email input
            'address': forms.Textarea(attrs=fc_ta),  # address textarea
            'status': forms.Select(attrs=fc),  # active/inactive dropdown
        }


# form to add or edit a medicine catalog entry
class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine  # this form is built from the medicine model
        fields = ['name', 'category', 'unit', 'manufacturer', 'reorder_level', 'description']  # fields shown on the form
        widgets = {
            'name': forms.TextInput(attrs=fc),  # medicine name input
            'category': forms.Select(attrs=fc),  # category dropdown
            'unit': forms.Select(attrs=fc),  # unit dropdown
            'manufacturer': forms.TextInput(attrs=fc),  # manufacturer input
            'reorder_level': forms.NumberInput(attrs=fc),  # reorder level input
            'description': forms.Textarea(attrs=fc_ta),  # description textarea
        }


# form to add or edit a medicine stock batch
class MedicineStockForm(forms.ModelForm):
    class Meta:
        model = MedicineStock  # this form is built from the medicine stock model
        fields = ['medicine', 'supplier', 'batch_number', 'quantity', 'purchase_price', 'expiry_date']  # fields shown on the form
        widgets = {
            'medicine': forms.Select(attrs=fc),  # medicine dropdown
            'supplier': forms.Select(attrs=fc),  # supplier dropdown
            'batch_number': forms.TextInput(attrs=fc),  # batch number input
            'quantity': forms.NumberInput(attrs=fc),  # quantity input
            'purchase_price': forms.NumberInput(attrs=fc),  # purchase price input
            'expiry_date': forms.DateInput(attrs=fc_date),  # expiry date picker
        }
