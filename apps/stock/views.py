# views for medicine catalog and stock batch management
from django.shortcuts import render, redirect, get_object_or_404  # helpers to render pages and redirect
from django.contrib import messages  # helper to show success/error messages
from django.contrib.auth.decorators import login_required  # decorator to require login
from datetime import date  # import date so the templates can block future expiry dates
from .models import Medicine, MedicineStock  # import our models
from .forms import MedicineForm, MedicineStockForm  # import our forms
from apps.supplier.models import Supplier  # suppliers are picked from a dropdown on the stock pages
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role

# role codes allowed to manage medicines and stock
STOCK_ROLES = ['admin', 'pharmacist']


# ── Medicine Management ───────────────────────────────────────────────────────

# show a list of all medicines in the catalog
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to view medicines.')
def medicine_list(request):
    medicines = Medicine.objects.all()  # get every medicine from the database
    return render(request, 'dashboard/medicine_inventory/medicine_list.html', {'medicines': medicines})


# add a new medicine to the catalog
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to add medicines.')
def medicine_add(request):
    medicine = Medicine()  # a blank medicine, only used so the template can show its default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = MedicineForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        medicine.name = request.POST.get('name', '')  # medicine name
        medicine.category = request.POST.get('category', '')  # tablet, syrup, etc
        medicine.unit = request.POST.get('unit', '')  # how the medicine is counted
        medicine.manufacturer = request.POST.get('manufacturer', '')  # company that makes it
        medicine.reorder_level = request.POST.get('reorder_level') or 10  # minimum quantity before reorder
        medicine.description = request.POST.get('description', '')  # extra notes
        medicine.save()  # write the new medicine to the database
        messages.success(request, f'Medicine "{medicine.name}" added successfully.')
        return redirect('medicine_list')

    return render(request, 'dashboard/medicine_inventory/medicine_add.html', {'form': form, 'medicine': medicine})


# edit an existing medicine
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to edit medicines.')
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)  # find the medicine or show a 404 page
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = MedicineForm(request.POST or None, instance=medicine)

    if request.method == 'POST' and form.is_valid():
        medicine.name = request.POST.get('name', '')  # medicine name
        medicine.category = request.POST.get('category', '')  # tablet, syrup, etc
        medicine.unit = request.POST.get('unit', '')  # how the medicine is counted
        medicine.manufacturer = request.POST.get('manufacturer', '')  # company that makes it
        medicine.reorder_level = request.POST.get('reorder_level') or 10  # minimum quantity before reorder
        medicine.description = request.POST.get('description', '')  # extra notes
        medicine.save()  # write the changes to the database
        messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
        return redirect('medicine_list')

    return render(request, 'dashboard/medicine_inventory/medicine_edit.html', {'form': form, 'medicine': medicine})


# show the details of one medicine, including its stock batches
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to view this medicine.')
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)  # find the medicine or show a 404 page
    batches = medicine.stock_batches.all()  # get all stock batches for this medicine
    return render(request, 'dashboard/medicine_inventory/medicine_detail.html', {'medicine': medicine, 'batches': batches})


# delete a medicine from the catalog
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to delete medicines.')
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)  # find the medicine or show a 404 page
    if request.method == 'POST':
        name = medicine.name  # remember the name before deleting
        medicine.delete()  # delete the medicine and its stock batches
        messages.success(request, f'Medicine "{name}" deleted successfully.')
        return redirect('medicine_list')
    return redirect('medicine_list')


# ── Stock Management ──────────────────────────────────────────────────────────

# show a list of all stock batches, this is the main real time inventory view
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to view stock.')
def stock_list(request):
    batches = MedicineStock.objects.select_related('medicine', 'supplier').all()  # get all batches with related data
    return render(request, 'dashboard/medicine_inventory/stock_list.html', {'batches': batches})


# add a new stock batch
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to add stock.')
def stock_add(request):
    batch = MedicineStock()  # a blank batch, only used so the template can show its default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = MedicineStockForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        batch.medicine_id = request.POST.get('medicine') or None  # which medicine this batch is for
        batch.supplier_id = request.POST.get('supplier') or None  # which supplier delivered this batch
        batch.batch_number = request.POST.get('batch_number', '')  # batch code on the packaging
        batch.quantity = request.POST.get('quantity') or 0  # how many units are in this batch
        batch.purchase_price = request.POST.get('purchase_price') or None  # price paid for this batch
        batch.expiry_date = request.POST.get('expiry_date') or None  # date this batch expires
        batch.save()  # write the new stock batch to the database
        messages.success(request, f'Stock batch "{batch.batch_number}" added successfully.')
        return redirect('stock_list')

    # every medicine and supplier, so the page can build the dropdown lists
    medicines = Medicine.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'dashboard/medicine_inventory/stock_add.html', {
        'form': form, 'batch': batch, 'medicines': medicines, 'suppliers': suppliers, 'today': date.today(),
    })


# edit an existing stock batch
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to edit stock.')
def stock_edit(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = MedicineStockForm(request.POST or None, instance=batch)

    if request.method == 'POST' and form.is_valid():
        batch.medicine_id = request.POST.get('medicine') or None  # which medicine this batch is for
        batch.supplier_id = request.POST.get('supplier') or None  # which supplier delivered this batch
        batch.batch_number = request.POST.get('batch_number', '')  # batch code on the packaging
        batch.quantity = request.POST.get('quantity') or 0  # how many units are in this batch
        batch.purchase_price = request.POST.get('purchase_price') or None  # price paid for this batch
        batch.expiry_date = request.POST.get('expiry_date') or None  # date this batch expires
        batch.save()  # write the changes to the database
        messages.success(request, f'Stock batch "{batch.batch_number}" updated successfully.')
        return redirect('stock_list')

    # every medicine and supplier, so the page can build the dropdown lists
    medicines = Medicine.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'dashboard/medicine_inventory/stock_edit.html', {
        'form': form, 'batch': batch, 'medicines': medicines, 'suppliers': suppliers, 'today': date.today(),
    })


# show the details of one stock batch
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to view this stock batch.')
def stock_detail(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    return render(request, 'dashboard/medicine_inventory/stock_detail.html', {'batch': batch})


# delete a stock batch
@login_required
@required_role(STOCK_ROLES, 'You do not have permission to delete stock.')
def stock_delete(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    if request.method == 'POST':
        batch_number = batch.batch_number  # remember the batch number before deleting
        batch.delete()  # delete the stock batch
        messages.success(request, f'Stock batch "{batch_number}" deleted successfully.')
        return redirect('stock_list')
    return redirect('stock_list')
