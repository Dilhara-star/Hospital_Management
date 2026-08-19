# forms for medicine catalog and stock batch management
from django import forms  # import django's form tools
from datetime import date  # import date to compare against today
from .models import Medicine, MedicineStock  # import our models


# form to check medicine catalog data is valid; the view saves the fields by hand
class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine  # this form is built from the medicine model
        fields = ['name', 'category', 'unit', 'manufacturer', 'reorder_level', 'description']  # fields checked by this form


# form to check a stock batch is valid; the view saves the fields by hand
class MedicineStockForm(forms.ModelForm):
    class Meta:
        model = MedicineStock  # this form is built from the medicine stock model
        fields = ['medicine', 'supplier', 'batch_number', 'quantity', 'purchase_price', 'expiry_date']  # fields checked by this form


