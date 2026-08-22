# forms for medicine catalog and stock batch management
from django import forms  # import django's form tools
from datetime import date  # import date to compare against today
from .models import Medicine, MedicineStock  # import our models


# form to check medicine catalog data is valid; the view saves the fields by hand
class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine  # this form is built from the medicine model
        fields = ['name', 'category', 'unit', 'manufacturer', 'reorder_level', 'description']  # fields checked by this form

    # the model allows category/unit/manufacturer to be blank, but a usable medicine
    # record needs all three, so this form makes them required
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = True
        self.fields['unit'].required = True
        self.fields['manufacturer'].required = True

    # stops a medicine name that is just spaces, or already used by another medicine
    def clean_name(self):
        # pull the cleaned name value out of the form, with extra spaces removed
        name = self.cleaned_data.get('name', '').strip()
        # stop if nothing is left after removing spaces
        if not name:
            raise forms.ValidationError('Please enter a medicine name.')
        # find any other medicine that already has this name
        query = Medicine.objects.filter(name__iexact=name)
        # do not count the medicine we are editing against itself
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        # stop if another medicine already has this name
        if query.exists():
            raise forms.ValidationError('A medicine with this name already exists.')
        # name is fine
        return name

    # stops a manufacturer name that is just spaces from being saved
    def clean_manufacturer(self):
        # pull the cleaned manufacturer value out of the form, with extra spaces removed
        manufacturer = self.cleaned_data.get('manufacturer', '').strip()
        # stop if nothing is left after removing spaces
        if not manufacturer:
            raise forms.ValidationError('Please enter the manufacturer.')
        # manufacturer is fine
        return manufacturer


# form to check a stock batch is valid; the view saves the fields by hand
class MedicineStockForm(forms.ModelForm):
    class Meta:
        model = MedicineStock  # this form is built from the medicine stock model
        fields = ['medicine', 'supplier', 'batch_number', 'quantity', 'purchase_price', 'expiry_date']  # fields checked by this form

    # stops a batch number that is just spaces from being saved
    def clean_batch_number(self):
        # pull the cleaned batch number value out of the form, with extra spaces removed
        batch_number = self.cleaned_data.get('batch_number', '').strip()
        # stop if nothing is left after removing spaces
        if not batch_number:
            raise forms.ValidationError('Please enter a batch number.')
        # batch number is fine
        return batch_number

    # stops an expiry date that is today or already in the past
    def clean_expiry_date(self):
        # pull the cleaned expiry date value out of the form
        expiry_date = self.cleaned_data.get('expiry_date')
        # stop if the date is today or earlier - a new batch must expire in the future
        if expiry_date and expiry_date <= date.today():
            raise forms.ValidationError('Expiry date must be in the future.')
        # date is fine
        return expiry_date

    # stops a purchase price of zero, negative, or blank from being saved
    def clean_purchase_price(self):
        # pull the cleaned purchase price value out of the form
        purchase_price = self.cleaned_data.get('purchase_price')
        # stop if it is missing or not greater than zero
        if not purchase_price or purchase_price <= 0:
            raise forms.ValidationError('Please enter a purchase price greater than zero.')
        # price is fine
        return purchase_price

    # stops a batch being added with zero quantity
    def clean_quantity(self):
        # pull the cleaned quantity value out of the form
        quantity = self.cleaned_data.get('quantity')
        # stop if it is missing or not greater than zero
        if not quantity or quantity <= 0:
            raise forms.ValidationError('Please enter a quantity greater than zero.')
        # quantity is fine
        return quantity

    # stops the same batch number being used twice for the same medicine
    def clean(self):
        # run the normal field checks first
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        batch_number = cleaned_data.get('batch_number')

        if medicine and batch_number:
            # find any other batch with the same medicine and batch number
            query = MedicineStock.objects.filter(medicine=medicine, batch_number__iexact=batch_number)
            # do not count the batch we are editing against itself
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            # stop if this medicine already has a batch with this number
            if query.exists():
                self.add_error('batch_number', 'This medicine already has a batch with this number.')

        # give back the checked data
        return cleaned_data
