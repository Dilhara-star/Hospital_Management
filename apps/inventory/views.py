# views for supplier and medicine inventory management
from django.shortcuts import render, redirect, get_object_or_404  # helpers to render pages and redirect
from django.contrib import messages  # helper to show success/error messages
from django.contrib.auth.decorators import login_required  # decorator to require login
from .models import Supplier, Medicine, MedicineStock  # import our models
from .forms import SupplierForm, MedicineForm, MedicineStockForm  # import our forms


# ── Supplier Management ───────────────────────────────────────────────────────

# show a list of all suppliers
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()  # get every supplier from the database
    return render(request, 'dashboard/supplier_management/supplier_list.html', {'suppliers': suppliers})


# add a new supplier
@login_required
def supplier_add(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)  # build the form from submitted data
        if form.is_valid():
            supplier = form.save()  # save the new supplier
            messages.success(request, f'Supplier "{supplier.name}" added successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm()  # show a blank form
    return render(request, 'dashboard/supplier_management/supplier_add.html', {'form': form})


# edit an existing supplier
@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)  # fill the form with submitted data
        if form.is_valid():
            form.save()  # save the changes
            messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)  # fill the form with current supplier data
    return render(request, 'dashboard/supplier_management/supplier_edit.html', {'form': form, 'supplier': supplier})


# show the details of one supplier
@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    return render(request, 'dashboard/supplier_management/supplier_detail.html', {'supplier': supplier})


# delete a supplier
@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    if request.method == 'POST':
        name = supplier.name  # remember the name before deleting
        supplier.delete()  # delete the supplier
        messages.success(request, f'Supplier "{name}" deleted successfully.')
        return redirect('supplier_list')
    return redirect('supplier_list')


# ── Medicine Management ───────────────────────────────────────────────────────

# show a list of all medicines in the catalog
@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()  # get every medicine from the database
    return render(request, 'dashboard/medicine_inventory/medicine_list.html', {'medicines': medicines})


# add a new medicine to the catalog
@login_required
def medicine_add(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)  # build the form from submitted data
        if form.is_valid():
            medicine = form.save()  # save the new medicine
            messages.success(request, f'Medicine "{medicine.name}" added successfully.')
            return redirect('medicine_list')
    else:
        form = MedicineForm()  # show a blank form
    return render(request, 'dashboard/medicine_inventory/medicine_add.html', {'form': form})


# edit an existing medicine
@login_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)  # find the medicine or show a 404 page
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)  # fill the form with submitted data
        if form.is_valid():
            form.save()  # save the changes
            messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)  # fill the form with current medicine data
    return render(request, 'dashboard/medicine_inventory/medicine_edit.html', {'form': form, 'medicine': medicine})


# show the details of one medicine, including its stock batches
@login_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)  # find the medicine or show a 404 page
    batches = medicine.stock_batches.all()  # get all stock batches for this medicine
    return render(request, 'dashboard/medicine_inventory/medicine_detail.html', {'medicine': medicine, 'batches': batches})


# delete a medicine from the catalog
@login_required
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
def stock_list(request):
    batches = MedicineStock.objects.select_related('medicine', 'supplier').all()  # get all batches with related data
    return render(request, 'dashboard/medicine_inventory/stock_list.html', {'batches': batches})


# add a new stock batch
@login_required
def stock_add(request):
    if request.method == 'POST':
        form = MedicineStockForm(request.POST)  # build the form from submitted data
        if form.is_valid():
            batch = form.save()  # save the new stock batch
            messages.success(request, f'Stock batch "{batch.batch_number}" added successfully.')
            return redirect('stock_list')
    else:
        form = MedicineStockForm()  # show a blank form
    return render(request, 'dashboard/medicine_inventory/stock_add.html', {'form': form})


# edit an existing stock batch
@login_required
def stock_edit(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    if request.method == 'POST':
        form = MedicineStockForm(request.POST, instance=batch)  # fill the form with submitted data
        if form.is_valid():
            form.save()  # save the changes
            messages.success(request, f'Stock batch "{batch.batch_number}" updated successfully.')
            return redirect('stock_list')
    else:
        form = MedicineStockForm(instance=batch)  # fill the form with current batch data
    return render(request, 'dashboard/medicine_inventory/stock_edit.html', {'form': form, 'batch': batch})


# show the details of one stock batch
@login_required
def stock_detail(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    return render(request, 'dashboard/medicine_inventory/stock_detail.html', {'batch': batch})


# delete a stock batch
@login_required
def stock_delete(request, pk):
    batch = get_object_or_404(MedicineStock, pk=pk)  # find the batch or show a 404 page
    if request.method == 'POST':
        batch_number = batch.batch_number  # remember the batch number before deleting
        batch.delete()  # delete the stock batch
        messages.success(request, f'Stock batch "{batch_number}" deleted successfully.')
        return redirect('stock_list')
    return redirect('stock_list')
