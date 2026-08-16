# views for supplier management
from django.shortcuts import render, redirect, get_object_or_404  # helpers to render pages and redirect
from django.contrib import messages  # helper to show success/error messages
from django.contrib.auth.decorators import login_required  # decorator to require login
from .models import Supplier  # import our model
from .forms import SupplierForm  # import our form
from .notifications import send_supplier_welcome_email  # emails a new supplier that they were added
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role

# role codes allowed to manage suppliers
SUPPLIER_ROLES = ['admin', 'pharmacist']


# show a list of all suppliers
@login_required
@required_role(SUPPLIER_ROLES, 'You do not have permission to view suppliers.')
def supplier_list(request):
    suppliers = Supplier.objects.all()  # get every supplier from the database
    return render(request, 'dashboard/supplier_management/supplier_list.html', {'suppliers': suppliers})


# add a new supplier
@login_required
@required_role(SUPPLIER_ROLES, 'You do not have permission to add suppliers.')
def supplier_add(request):
    supplier = Supplier()  # a blank supplier, only used so the template can show its default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = SupplierForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # fill the blank supplier in field by field from the posted data
        supplier.name = request.POST.get('name', '')  # supplier company name
        supplier.contact_person = request.POST.get('contact_person', '')  # main contact person
        supplier.phone = request.POST.get('phone', '')  # phone number
        supplier.email = request.POST.get('email', '')  # email address
        supplier.address = request.POST.get('address', '')  # postal address
        supplier.status = request.POST.get('status', 'active')  # active or inactive
        supplier.save()  # write the new supplier to the database
        send_supplier_welcome_email(supplier)  # let the supplier know they were added
        messages.success(request, f'Supplier "{supplier.name}" added successfully.')
        return redirect('supplier_list')

    return render(request, 'dashboard/supplier_management/supplier_add.html', {'form': form, 'supplier': supplier})


# edit an existing supplier
@login_required
@required_role(SUPPLIER_ROLES, 'You do not have permission to edit suppliers.')
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = SupplierForm(request.POST or None, instance=supplier)

    if request.method == 'POST' and form.is_valid():
        supplier.name = request.POST.get('name', '')  # supplier company name
        supplier.contact_person = request.POST.get('contact_person', '')  # main contact person
        supplier.phone = request.POST.get('phone', '')  # phone number
        supplier.email = request.POST.get('email', '')  # email address
        supplier.address = request.POST.get('address', '')  # postal address
        supplier.status = request.POST.get('status', 'active')  # active or inactive
        supplier.save()  # write the changes to the database
        messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
        return redirect('supplier_list')

    return render(request, 'dashboard/supplier_management/supplier_edit.html', {'form': form, 'supplier': supplier})


# show the details of one supplier
@login_required
@required_role(SUPPLIER_ROLES, 'You do not have permission to view this supplier.')
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    return render(request, 'dashboard/supplier_management/supplier_detail.html', {'supplier': supplier})


# delete a supplier
@login_required
@required_role(SUPPLIER_ROLES, 'You do not have permission to delete suppliers.')
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)  # find the supplier or show a 404 page
    if request.method == 'POST':
        name = supplier.name  # remember the name before deleting
        supplier.delete()  # delete the supplier
        messages.success(request, f'Supplier "{name}" deleted successfully.')
        return redirect('supplier_list')
    return redirect('supplier_list')
