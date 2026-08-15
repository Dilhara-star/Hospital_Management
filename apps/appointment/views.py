from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator  # splits a long medicine list into pages
from django.db import transaction  # keeps stock updates safe when two requests happen at the same time
from django.db.models import F  # lets us update a number based on its own current value in the database
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone  # used to stamp when a payment was paid
from .models import Appointment, DepartmentFee, Payment, PrescriptionItem, PharmacyOrder
from .forms import AppointmentForm, StaffAppointmentForm, PaymentForm, AppointmentEditForm
from .notifications import send_appointment_confirmation_email  # emails the patient once an appointment is confirmed
from apps.inventory.models import Medicine, MedicineStock  # the pharmacy catalog the doctor picks medicine from
from apps.user_management.models import StaffProfile  # holds the room number and hourly fee for a doctor
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role


def _doctor_room(doctor):
    # the room number the receptionist assigned to this doctor, or '' if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return ''
    try:
        return doctor.staff_profile.room_number
    except StaffProfile.DoesNotExist:
        return ''


def _doctor_fee(doctor):
    # this doctor's own consultation fee, or 0 if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return 0
    try:
        return doctor.staff_profile.hourly_fee
    except StaffProfile.DoesNotExist:
        return 0


def _record_payment(appointment, payment_method, paid_now=False):
    # shared by the patient booking form and the staff "Add Appointment" page.
    # paid_now covers cash that's handed over right at the reception desk.
    if payment_method == 'online':
        paid_now = True  # online payments are always paid immediately

    # look up the fee for this department, default to 0 if staff haven't set one yet
    fee_row = DepartmentFee.objects.filter(department=appointment.department).first()
    department_fee = fee_row.fee if fee_row else 0
    doctor_fee = _doctor_fee(appointment.doctor)  # this doctor's own cut
    fee_amount = department_fee + doctor_fee  # total the patient pays

    if paid_now:
        appointment.status = 'confirmed'  # money is in, so confirm right away
        appointment.save()

    ref_prefix = 'PAY' if payment_method == 'online' else 'CASH'  # demo receipt number style
    Payment.objects.create(
        appointment=appointment,  # link the payment to this appointment
        amount=fee_amount,  # department fee + doctor fee
        doctor_fee_amount=doctor_fee,  # snapshot of just the doctor's cut, used later in revenue reports
        method=payment_method,  # 'online' or 'cash'
        status='paid' if paid_now else 'pending',
        paid_at=timezone.now() if paid_now else None,  # paid time, if any
        transaction_ref=f'{ref_prefix}-{appointment.pk:06d}' if paid_now else '',
    )

    if paid_now:
        send_appointment_confirmation_email(appointment)  # let the patient know their appointment is confirmed


@login_required
def appointment_index(request):
    # doctors only see the appointments assigned to them; other staff see every appointment
    if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
        appointments = Appointment.objects.filter(doctor=request.user)
    else:
        appointments = Appointment.objects.all()
    return render(request, 'dashboard/appointment_management/index.html', {'appointments': appointments})


def appointment_form(request):
    # anyone can view and fill this page, no login needed
    appointment = Appointment()  # a blank appointment, only used so the template can show default field values
    if request.user.is_authenticated:
        # fill the name field with the logged in user's name, to save typing
        appointment.patient_name = request.user.get_full_name()

    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = AppointmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        if not request.user.is_authenticated:
            # we cannot save a booking without a logged in user, so ask them to log in
            messages.error(request, 'Please log in or sign up to complete your booking.')
        else:
            # 'online' or 'cash', chosen on the payment step of the form
            payment_method = request.POST.get('payment_method', 'cash')

            appointment.patient = request.user  # attach the logged in user as the patient
            appointment.department = request.POST.get('department', '')
            appointment.date = request.POST.get('date', '')
            appointment.time_slot = request.POST.get('time_slot', '')
            appointment.doctor_id = request.POST.get('doctor') or None
            appointment.message = request.POST.get('message', '')
            appointment.patient_name = request.POST.get('patient_name', '')
            appointment.patient_contact = request.POST.get('patient_contact', '')
            appointment.patient_age = request.POST.get('patient_age') or 0
            appointment.patient_address = request.POST.get('patient_address', '')
            appointment.patient_nic = request.POST.get('patient_nic', '')
            appointment.save()  # save the appointment so it has an id

            _record_payment(appointment, payment_method)

            if payment_method == 'online':
                messages.success(request, 'Payment received. Your appointment is confirmed!')
            else:
                messages.success(request, 'Appointment booked. Please pay at the hospital reception to confirm it.')
            return redirect('appointment_form')

    # fee for every department, shown on the payment step of the form
    fees = {row.department: str(row.fee) for row in DepartmentFee.objects.all()}
    # every active doctor, so the page can build the doctor dropdown
    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')
    # each doctor's own hourly fee, added on top of the department fee on the payment step
    doctor_fees = {str(doctor.pk): str(_doctor_fee(doctor)) for doctor in doctors}
    return render(request, 'frontend/appointment/form.html', {
        'form': form, 'appointment': appointment, 'fees': fees, 'doctors': doctors, 'doctor_fees': doctor_fees,
    })


@login_required
def my_appointments(request, pk=None):
    # only appointments that belong to the logged in patient, doctor name attached in the same query
    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor')

    # split the sidebar list into pages of 10, so it never grows too long
    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    if pk:
        # patient picked one appointment from the sidebar; 404 if it is not theirs
        selected_appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    else:
        # nothing picked yet, default to the most recent appointment
        selected_appointment = appointments.first()

    # medicines prescribed for the selected appointment, with medicine details attached
    prescribed_items = []
    pharmacy_order = None
    medicine_total = 0
    doctor_room = ''
    if selected_appointment:
        prescribed_items = selected_appointment.prescription_items.select_related('medicine').all()
        doctor_room = _doctor_room(selected_appointment.doctor)  # room number, so the patient knows where to go
        if prescribed_items:
            # create the bill row the first time the patient looks at it, so they can pay
            # online right away without waiting for the pharmacist to open the queue first
            pharmacy_order, _created = PharmacyOrder.objects.get_or_create(appointment=selected_appointment)
            # worked out fresh from the catalog price, so it is correct even before the order is dispensed
            medicine_total = sum(item.medicine.price * item.quantity for item in prescribed_items)

    return render(request, 'frontend/appointment/my_appointments.html', {
        'page_obj': page_obj,
        'selected_appointment': selected_appointment,
        'prescribed_items': prescribed_items,
        'pharmacy_order': pharmacy_order,
        'medicine_total': medicine_total,
        'doctor_room': doctor_room,
    })


def appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # find the appointment or show a 404 page
    doctor_room = _doctor_room(appointment.doctor)  # room number, shown alongside the doctor's name
    return render(request, 'dashboard/appointment_management/view.html', {
        'appointment': appointment,
        'doctor_room': doctor_room,
    })


@login_required
def appointment_add(request):
    # lets staff register an appointment on a patient's behalf (e.g. phone or walk-in booking)
    appointment = Appointment(status='pending')  # a blank appointment, only used so the template can show default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = StaffAppointmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # appointments registered from the dashboard are always paid in cash at the hospital;
        # this checkbox just says whether the cash was already handed over
        cash_received = request.POST.get('cash_received') == 'yes'

        appointment.patient_id = request.POST.get('patient') or None
        appointment.department = request.POST.get('department', '')
        appointment.date = request.POST.get('date', '')
        appointment.time_slot = request.POST.get('time_slot', '')
        appointment.doctor_id = request.POST.get('doctor') or None
        appointment.message = request.POST.get('message', '')
        appointment.status = request.POST.get('status', 'pending')
        appointment.patient_name = request.POST.get('patient_name', '')
        appointment.patient_contact = request.POST.get('patient_contact', '')
        appointment.patient_age = request.POST.get('patient_age') or 0
        appointment.patient_address = request.POST.get('patient_address', '')
        appointment.patient_nic = request.POST.get('patient_nic', '')
        appointment.save()

        _record_payment(appointment, 'cash', paid_now=cash_received)
        messages.success(request, 'Appointment has been registered.')
        return redirect('appointment_index')

    # every active patient/doctor, so the page can build the patient and doctor dropdowns
    patients = User.objects.filter(profile__role='patient', is_active=True).order_by('first_name', 'last_name')
    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')
    return render(request, 'dashboard/appointment_management/add.html', {
        'form': form, 'appointment': appointment, 'patients': patients, 'doctors': doctors,
    })


@login_required
def appointment_edit(request, pk):
    # the doctor assigned to this appointment gets a read-only details view plus
    # a pharmacy section to prescribe medicine. everyone else (reception/admin)
    # gets the full edit form, unchanged.
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.doctor == request.user:
        return _prescribe_medicine(request, appointment)

    # the Payment linked to this appointment; build a blank one if it doesn't have one yet (old appointments)
    payment = getattr(appointment, 'payment', None) or Payment(appointment=appointment)

    # a prefix keeps this form's "status" field from clashing with the appointment form's own "status" field.
    # both forms are only used to check the typed data is valid; the actual save is done by hand below
    form = StaffAppointmentForm(request.POST or None, instance=appointment)
    payment_form = PaymentForm(request.POST or None, instance=payment, prefix='payment')

    if request.method == 'POST' and form.is_valid() and payment_form.is_valid():
        appointment.patient_id = request.POST.get('patient') or None
        appointment.department = request.POST.get('department', '')
        appointment.date = request.POST.get('date', '')
        appointment.time_slot = request.POST.get('time_slot', '')
        appointment.doctor_id = request.POST.get('doctor') or None
        appointment.message = request.POST.get('message', '')
        appointment.status = request.POST.get('status', 'pending')
        appointment.patient_name = request.POST.get('patient_name', '')
        appointment.patient_contact = request.POST.get('patient_contact', '')
        appointment.patient_age = request.POST.get('patient_age') or 0
        appointment.patient_address = request.POST.get('patient_address', '')
        appointment.patient_nic = request.POST.get('patient_nic', '')
        appointment.save()

        payment.appointment = appointment  # needed the first time, if there was no payment yet
        payment.amount = request.POST.get('payment-amount') or 0
        payment.method = request.POST.get('payment-method', 'cash')
        payment.status = request.POST.get('payment-status', 'pending')
        if payment.status == 'paid' and not payment.paid_at:
            payment.paid_at = timezone.now()  # stamp the first time it's marked paid
        payment.save()

        messages.success(request, 'Appointment has been updated.')
        return redirect('appointment_view', pk=appointment.pk)

    # every active patient/doctor, so the page can build the patient and doctor dropdowns
    patients = User.objects.filter(profile__role='patient', is_active=True).order_by('first_name', 'last_name')
    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')
    return render(request, 'dashboard/appointment_management/edit.html', {
        'form': form, 'payment_form': payment_form, 'appointment': appointment, 'payment': payment,
        'patients': patients, 'doctors': doctors, 'is_doctor_view': False,
    })


def _is_ajax(request):
    # jQuery sets this header automatically on every $.post / $.get call
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _prescribed_items_response(request, appointment):
    # renders just the "Prescribed for This Visit" table, used by the ajax add/remove views
    prescribed_items = appointment.prescription_items.select_related('medicine').all()
    return render(request, 'dashboard/appointment_management/_prescribed_items.html', {
        'appointment': appointment,
        'prescribed_items': prescribed_items,
    })


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


def _prescribe_medicine(request, appointment):
    # doctor-only branch of the edit page: no appointment/payment form, just the pharmacy section
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
        messages.success(request, f'{medicine.name} added to the prescription.')
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


@login_required
def appointment_pharmacy_search(request, pk):
    # ajax endpoint for the pharmacy section's live search box.
    # it renders just the medicine list, not the whole page, so the page never reloads.
    appointment = get_object_or_404(Appointment, pk=pk)  # which appointment the doctor is prescribing for
    medicines_page, search_query, category = _search_medicines(request)  # same filtering as the full page
    return render(request, 'dashboard/appointment_management/_pharmacy_list.html', {
        'appointment': appointment,
        'medicines': medicines_page,
        'search_query': search_query,
        'category': category,
    })


def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # find the appointment or show a 404 page
    appointment.delete()
    messages.success(request, 'Your appointment has been deleted.')
    return redirect('appointment_index')


@login_required
def prescription_item_delete(request, pk, item_pk):
    # lets the assigned doctor remove a medicine they added to this prescription by mistake
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


@login_required
@required_role(['admin', 'receptionist'], 'You do not have permission to confirm payments.', 'appointment_index')
def confirm_cash_payment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # find the appointment or show a 404 page
    payment = getattr(appointment, 'payment', None)  # the Payment linked to this appointment, if any

    if payment and payment.method == 'cash' and payment.status == 'pending':
        payment.status = 'paid'  # mark the cash payment as received
        payment.paid_at = timezone.now()  # stamp the time it was received
        payment.transaction_ref = f'CASH-{appointment.pk:06d}'  # fake receipt number
        payment.save()

        appointment.status = 'confirmed'  # cash is in, so confirm the appointment
        appointment.save()
        send_appointment_confirmation_email(appointment)  # let the patient know their appointment is confirmed
        messages.success(request, 'Cash payment confirmed. The appointment is now confirmed.')

    return redirect('appointment_view', pk=appointment.pk)


@login_required
@required_role(['admin', 'receptionist'], 'You do not have permission to manage fees.')
def fee_index(request):
    if request.method == 'POST':
        # go through every real department (skip the blank "Select Department" choice)
        for code, label in Appointment.DEPARTMENT_CHOICES:
            if not code:
                continue
            fee_value = request.POST.get(f'fee_{code}', '0')  # value typed for this department
            DepartmentFee.objects.update_or_create(department=code, defaults={'fee': fee_value})
        messages.success(request, 'Consultation fees have been updated.')
        return redirect('fee_index')

    # current fee for each department, so the form can show existing prices
    existing_fees = {row.department: row.fee for row in DepartmentFee.objects.all()}
    departments = []
    for code, label in Appointment.DEPARTMENT_CHOICES:
        if not code:
            continue
        departments.append({'code': code, 'label': label, 'fee': existing_fees.get(code, 0)})

    return render(request, 'dashboard/fee_management/index.html', {'departments': departments})


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
            messages.success(request, 'Medicine has been given to the patient.')

        elif action == 'record_payment' and order.status != 'completed' and order.payment_status == 'pending':
            payment_method = request.POST.get('payment_method', 'cash')  # 'online' or 'cash'
            ref_prefix = 'PAY' if payment_method == 'online' else 'CASH'  # demo receipt number style
            order.payment_method = payment_method
            order.payment_status = 'paid'
            order.paid_at = timezone.now()
            order.transaction_ref = f'{ref_prefix}-{appointment.pk:06d}'
            order.save()
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


@login_required
def pay_medicine_online(request, pk):
    # lets the patient pay for their medicine online, from the "My Appointments" page
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    order = getattr(appointment, 'pharmacy_order', None)  # may not exist yet if nothing was prescribed

    if request.method == 'POST' and order and order.status != 'completed' and order.payment_status == 'pending':
        order.payment_method = 'online'
        order.payment_status = 'paid'
        order.paid_at = timezone.now()
        order.transaction_ref = f'PAY-{appointment.pk:06d}'
        order.save()
        messages.success(request, 'Payment received. Thank you!')

    return redirect('my_appointment_detail', pk=appointment.pk)


# lets a patient reschedule the date and time of their own appointment
@login_required
def edit_appointment(request, pk):
    # only the logged in patient who owns this appointment may edit it; 404 if it is not theirs
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    # form is only used to check the new date/time slot are valid; the actual save is done by hand below
    form = AppointmentEditForm(request.POST or None, instance=appointment)

    # if the form is invalid, this whole block is skipped and we fall through to the render
    # below, which shows the page again with the error messages
    if request.method == 'POST' and form.is_valid():
        appointment.date = request.POST.get('date', '')
        appointment.time_slot = request.POST.get('time_slot', '')
        appointment.save()
        messages.success(request, 'Appointment updated successfully.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    return render(request, 'frontend/appointment/edit_appointment.html', {
        'form': form, 'appointment': appointment,
    })
