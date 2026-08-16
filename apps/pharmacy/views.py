from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # splits a long medicine list into pages
from django.db import transaction  # keeps stock updates safe when two requests happen at the same time
from django.db.models import F  # lets us update a number based on its own current value in the database
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string  # turns a template into an html string, used for pdf bills
from django.http import HttpResponse  # used to send a pdf file back as the response
from django.utils import timezone  # used to stamp when a payment was paid
from apps.appointment.models import Appointment
from apps.stock.models import Medicine, MedicineStock
from apps.stock.notifications import send_email_to_admin_low_stock, send_email_to_supplier_low_stock
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role
from apps.user_management.models import StaffProfile  # holds the room number for a doctor
from .models import PrescriptionItem, PharmacyOrder
from .notifications import send_medicine_dispensed_email, send_medicine_payment_confirmation_email


# ── Dashboard ────────────────────────────────────────────────────────────────

# looks up a doctor's assigned room number, or '' if none has been set yet
def _doctor_room(doctor):
    if not doctor or not hasattr(doctor, 'profile'):
        return ''
    try:
        return doctor.staff_profile.room_number
    except StaffProfile.DoesNotExist:
        return ''


# true only if this request came from an ajax call, not a normal page load
def _is_ajax(request):
    # jQuery sets this header automatically on every $.post / $.get call
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


# renders just the "Prescribed for This Visit" table partial, used by the ajax add/remove views
def _prescribed_items_response(request, appointment):
    prescribed_items = appointment.prescription_items.select_related('medicine').all()
    return render(request, 'dashboard/appointment_management/_prescribed_items.html', {
        'appointment': appointment,
        'prescribed_items': prescribed_items,
    })


# filters and paginates the medicine catalog for the pharmacy search box
def _search_medicines(request):
    # search box and category dropdown on the pharmacy section, both optional
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    medicines = Medicine.objects.all().order_by('name')  # start from the full catalog, same one /inventory/medicines/ shows
    if search_query:
        medicines = medicines.filter(name__icontains=search_query)  # keep only names containing the search text
    if category:
        medicines = medicines.filter(category=category)  # keep only the chosen category

    # split the medicine list into pages of 5, so the pharmacy section doesn't get too long
    paginator = Paginator(medicines, 5)
    page_number = request.GET.get('page')  # which page the doctor asked for
    medicines_page = paginator.get_page(page_number)  # falls back to page 1 if missing or invalid

    return medicines_page, search_query, category  # give back the page of results plus what was searched for


# doctor's "prescribe medicine" screen, shown instead of the normal edit form on the
# doctor's own appointments (called from apps.appointment.views.appointment_edit)
def prescribe_medicine_for_appointment(request, appointment):
    if request.method == 'POST':
        medicine = get_object_or_404(Medicine, pk=request.POST.get('medicine_id'))  # the medicine the doctor picked
        PrescriptionItem.objects.create(
            appointment=appointment,
            medicine=medicine,
            dosage=request.POST.get('dosage', ''),
            quantity=request.POST.get('quantity') or 1,
            instructions=request.POST.get('instructions', ''),
        )
        if _is_ajax(request):
            return _prescribed_items_response(request, appointment)  # just refresh the table, no page reload

        return redirect('appointment_edit', pk=appointment.pk)

    medicines_page, search_query, category = _search_medicines(request)  # filtered + paginated medicine list

    # medicines already prescribed for this visit, oldest pick first
    prescribed_items = appointment.prescription_items.select_related('medicine').all()

    return render(request, 'dashboard/appointment_management/edit.html', {
        'appointment': appointment,
        'is_doctor_view': True,
        'medicines': medicines_page,
        'prescribed_items': prescribed_items,
        'search_query': search_query,
        'category': category,
        'category_choices': Medicine.CATEGORY_CHOICES,
        'doctor_room': _doctor_room(appointment.doctor),
    })


# ajax endpoint for the pharmacy section's live search box; returns just the medicine list
@login_required
@required_role(['admin', 'doctor', 'pharmacist'], 'You do not have permission to search the pharmacy catalog.')
def appointment_pharmacy_search(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # which appointment the doctor is prescribing for
    medicines_page, search_query, category = _search_medicines(request)  # same filtering as the full page
    return render(request, 'dashboard/pharmacy_management/_pharmacy_list.html', {
        'appointment': appointment,
        'medicines': medicines_page,
        'search_query': search_query,
        'category': category,
    })


# lets the assigned doctor remove a medicine they added to this prescription by mistake
@login_required
def prescription_item_delete(request, pk, item_pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.doctor != request.user:
        messages.error(request, 'You do not have permission to edit this prescription.')
        return redirect('appointment_index')

    if request.method == 'POST':
        item = get_object_or_404(PrescriptionItem, pk=item_pk, appointment=appointment)  # must belong to this appointment
        item.delete()
        if _is_ajax(request):
            return _prescribed_items_response(request, appointment)  # just refresh the table, no page reload
        messages.success(request, 'Medicine removed from the prescription.')

    return redirect('appointment_edit', pk=appointment.pk)


# pharmacist's queue: every appointment with prescribed medicine still awaiting dispensing/payment
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view the pharmacy counter.')
def pharmacy_queue(request):
    # appointments that have prescribed medicine and are not completed yet
    appointments = Appointment.objects.filter(
        prescription_items__isnull=False,
    ).exclude(
        pharmacy_order__status='completed',
    ).distinct().select_related('patient', 'doctor').prefetch_related('prescription_items__medicine').order_by('-created_at')

    # split the queue into pages of 10, so it never grows too long
    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/pharmacy_management/queue.html', {'page_obj': page_obj})


# pharmacist screen: dispense the prescribed medicine (takes it out of stock), then record its payment
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view the pharmacy counter.')
def pharmacy_order_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    # make the order row the first time anyone opens this appointment's pharmacy page
    order, _created = PharmacyOrder.objects.get_or_create(appointment=appointment)

    prescribed_items = appointment.prescription_items.select_related('medicine').all()
    # total price of every prescribed item, worked out fresh each time from the current catalog price
    total_amount = sum(item.medicine.price * item.quantity for item in prescribed_items)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'dispense' and order.status == 'pending':
            # give out the medicine and take it out of stock, batch by batch, oldest expiry first
            with transaction.atomic():
                for item in prescribed_items:
                    remaining = item.quantity  # how many units of this medicine we still need to take
                    batches = item.medicine.stock_batches.select_for_update().filter(quantity__gt=0)
                    for batch in batches:
                        if remaining <= 0:
                            break
                        take = min(remaining, batch.quantity)  # do not take more than this batch has left
                        MedicineStock.objects.filter(pk=batch.pk).update(quantity=F('quantity') - take)
                        remaining -= take

                order.total_amount = total_amount
                order.status = 'dispensed'
                order.dispensed_by = request.user
                order.dispensed_at = timezone.now()
                order.save()

            send_medicine_dispensed_email(order)  # let the patient know their medicine is ready and awaiting payment

            # check each dispensed medicine's stock and alert admin/supplier if it is low
            for item in prescribed_items:
                remaining_stock = item.medicine.total_quantity  # fresh total after the deduction above
                if remaining_stock <= 100:
                    send_email_to_admin_low_stock(item.medicine, remaining_stock)
                if remaining_stock <= 50:
                    send_email_to_supplier_low_stock(item.medicine, remaining_stock)

            messages.success(request, 'Medicine has been given to the patient.')

        elif action == 'record_payment' and order.status != 'completed' and order.payment_status == 'pending':
            payment_method = 'cash'  # this counter only ever records cash - online is paid by the patient themselves
            ref_prefix = 'CASH'  # demo receipt number style
            order.payment_method = payment_method
            order.payment_status = 'paid'
            order.paid_at = timezone.now()
            order.transaction_ref = f'{ref_prefix}-{appointment.pk:06d}'
            order.save()
            send_medicine_payment_confirmation_email(order)  # let the patient know their medicine payment was recorded
            messages.success(request, 'Payment has been recorded.')

        elif action == 'complete' and order.status == 'dispensed' and order.payment_status == 'paid':
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()
            messages.success(request, 'Order marked as completed.')
            return redirect('pharmacy_queue')

        else:
            messages.error(request, 'That action cannot be done right now.')

        return redirect('pharmacy_order_detail', pk=appointment.pk)

    return render(request, 'dashboard/pharmacy_management/order_detail.html', {
        'appointment': appointment,
        'order': order,
        'prescribed_items': prescribed_items,
        'total_amount': total_amount,
    })


# ── Frontend ───────────────────────────────────────────────────────────────

# lets the patient pay for their medicine online, from the "My Appointments" page
@login_required
def pay_medicine_online(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    order = getattr(appointment, 'pharmacy_order', None)  # may not exist yet if nothing was prescribed

    if request.method == 'POST' and order and order.status != 'completed' and order.payment_status == 'pending':
        order.payment_method = 'online'
        order.payment_status = 'paid'
        order.paid_at = timezone.now()
        order.transaction_ref = f'PAY-{appointment.pk:06d}'
        order.save()
        send_medicine_payment_confirmation_email(order)  # let the patient know their medicine payment went through
        messages.success(request, 'Payment received. Thank you!')

    return redirect('my_appointment_detail', pk=appointment.pk)


# lets a patient download a pdf bill for the medicine they already paid for
@login_required
def download_medicine_bill(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)  # 404 if this isn't their own appointment
    order = getattr(appointment, 'pharmacy_order', None)  # the pharmacy order linked to this appointment, if any

    if not order or order.payment_status != 'paid':
        # nothing paid yet, so there is no bill to give out
        messages.error(request, 'This medicine order has no paid bill yet.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    prescribed_items = appointment.prescription_items.select_related('medicine').all()  # medicines on this order, with prices attached
    billed_items = []  # one row per medicine, with its unit price and subtotal worked out
    for item in prescribed_items:
        unit_price = item.medicine.price  # current catalog price for this medicine
        billed_items.append({
            'name': item.medicine.name,
            'quantity': item.quantity,
            'unit_price': unit_price,
            'subtotal': unit_price * item.quantity,
        })
    medicine_total = sum(row['subtotal'] for row in billed_items)  # total of every row above

    from xhtml2pdf import pisa  # html to pdf library, only needed here so it is imported at this point
    html = render_to_string('frontend/pharmacy/medicine_bill_pdf.html', {
        'appointment': appointment,
        'order': order,
        'billed_items': billed_items,
        'medicine_total': medicine_total,
    })
    response = HttpResponse(content_type='application/pdf')  # tell the browser this is a pdf file
    response['Content-Disposition'] = f'attachment; filename="bill_{order.transaction_ref}.pdf"'  # force a download prompt
    pisa.CreatePDF(html, dest=response)  # turn the html into a pdf and write it into the response
    return response
