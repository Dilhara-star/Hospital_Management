import re  # used to strip a phone number down to digits, for building a call-in patient's username
from datetime import datetime, timedelta  # used to work out the 24 hour appointment cancel cutoff
from decimal import Decimal  # turns the posted amount text into a real decimal number
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator  # splits a long appointment list into pages
from django.db.models import Q  # lets the payment search box match name OR transaction ref
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string  # turns a template into an html string, used for pdf bills
from django.http import HttpResponse  # used to send a pdf file back as the response
from django.utils import timezone  # used to stamp when a payment was paid
from .models import Appointment, DepartmentFee, DoctorAvailability, Payment
from .forms import AppointmentForm, StaffAppointmentForm, PaymentForm, AppointmentEditForm
from .notifications import (
    send_appointment_confirmation_email, send_appointment_confirmation_email_admin,
    send_email_appointment_without_payment, send_appointment_update_email,
    send_appointment_cancellation_email, send_appointment_refund_email, send_doctor_assignment_email,
)  # emails the patient once an appointment is confirmed, updated, cancelled, or refunded
from apps.pharmacy.models import PharmacyOrder  # the medicine order linked to an appointment
from apps.pharmacy.views import prescribe_medicine_for_appointment  # doctor's "prescribe medicine" screen
from apps.user_management.models import StaffProfile, UserProfile, PatientProfile  # doctor employment info, and patient account records
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role


# ── Shared Helpers ───────────────────────────────────────────────────────────

# looks up a doctor's assigned room number, or '' if none has been set yet
def _doctor_room(doctor):
    # the room number the receptionist assigned to this doctor, or '' if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return ''
    try:
        return doctor.staff_profile.room_number
    except StaffProfile.DoesNotExist:
        return ''


# looks up a doctor's own consultation fee, or 0 if none has been set yet
def _doctor_fee(doctor):
    # this doctor's own consultation fee, or 0 if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return 0
    try:
        return doctor.staff_profile.hourly_fee
    except StaffProfile.DoesNotExist:
        return 0


# finds an existing patient account by phone number, or creates a lightweight one if none
# exists yet - used when reception registers an appointment for a caller over the phone
def _find_or_create_call_in_patient(patient_name, patient_contact):
    # reuse the account if this phone number already belongs to a patient
    existing = User.objects.filter(profile__role='patient', profile__phone=patient_contact).first()
    if existing:
        return existing

    # split "Jane Doe" into first name "Jane" and last name "Doe"
    name_parts = patient_name.strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # build a username out of the phone number's digits, e.g. "patient0771234567"
    base_username = 'patient' + re.sub(r'\D', '', patient_contact)
    username = base_username
    suffix = 1
    # keep trying a new suffix until the username is free
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base_username}{suffix}'

    # step 1: create the login account - no usable password yet, since reception is
    # filling this in on the caller's behalf, not the patient themself
    patient_user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
    patient_user.set_unusable_password()
    patient_user.save()
    # step 2: create their basic profile
    UserProfile.objects.create(user=patient_user, phone=patient_contact, role='patient')
    # step 3: create their medical/insurance record
    PatientProfile.objects.create(user=patient_user, status='active')
    return patient_user


# looks up the department a doctor belongs to, or '' if none has been set yet
def _doctor_department(doctor):
    if not doctor or not hasattr(doctor, 'profile'):
        return ''
    try:
        return doctor.staff_profile.department
    except StaffProfile.DoesNotExist:
        return ''


# builds the exact datetime an appointment starts, used for the 24 hour cancel/refund cutoff
def _appointment_start_datetime(appointment):
    # time_slot looks like '09:00-10:00' - split on the dash and keep the start half
    start_text = appointment.time_slot.split('-')[0]
    # turn '09:00' into a plain time object
    start_time = datetime.strptime(start_text, '%H:%M').time()
    # combine the appointment's date with that start time into one datetime
    naive_datetime = datetime.combine(appointment.date, start_time)
    # make it timezone-aware, so it can be compared against timezone.now()
    return timezone.make_aware(naive_datetime)


# creates the Payment row for an appointment, confirming it and emailing out if paid now
def _create_appointment_payment_record(appointment, payment_method, paid_now=False):
    # shared by the patient booking form and the staff "Add Appointment" page.
    # paid_now covers cash that's handed over right at the reception desk.
    if payment_method == 'online':
        paid_now = True  # online payments are always paid immediately

    # look up the fee for this department, default to 0 if staff haven't set one yet
    fee_row = DepartmentFee.objects.filter(department=appointment.department).first()
    department_fee = fee_row.fee if fee_row else 0
    doctor_fee = _doctor_fee(appointment.doctor)  # this doctor's own cut
    fee_amount = department_fee + doctor_fee  # total the patient pays

    # children below 10 years old get 10% off the total fee
    # patient_age may still be the raw text typed on the booking form here, so convert it to a number first
    discount_amount = Decimal('0')
    if int(appointment.patient_age) < 10:
        discount_amount = (fee_amount * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% of the total, rounded to cents
    fee_amount = fee_amount - discount_amount  # final amount the patient pays, after discount

    if paid_now:
        appointment.status = 'confirmed'  # money is in, so confirm right away
        appointment.save()

    ref_prefix = 'PAY' if payment_method == 'online' else 'CASH'  # demo receipt number style
    Payment.objects.create(
        appointment=appointment,  # link the payment to this appointment
        amount=fee_amount,  # department fee + doctor fee, after discount
        doctor_fee_amount=doctor_fee,  # snapshot of just the doctor's cut, used later in revenue reports
        discount_amount=discount_amount,  # how much was taken off for the age discount, so the bill can show it
        method=payment_method,  # 'online' or 'cash'
        status='paid' if paid_now else 'pending',
        paid_at=timezone.now() if paid_now else None,  # paid time, if any
        transaction_ref=f'{ref_prefix}-{appointment.pk:06d}' if paid_now else '',
    )

    if paid_now:
        send_appointment_confirmation_email(appointment)  # let the patient know their appointment is confirmed
        send_appointment_confirmation_email_admin(appointment)  # let the staff know a new appointment has been booked


# ── Dashboard ────────────────────────────────────────────────────────────────

# lets a doctor pick which of the fixed one hour time slots they are available in,
# so the public booking form only offers patients slots this doctor actually works
@login_required
@required_role(['doctor'], 'You do not have permission to view this page.')
def doctor_settings(request):
    doctor = request.user  # only doctors can reach this page, and only for their own slots

    if request.method == 'POST':
        # every slot checkbox the doctor ticked, e.g. ['09:00-10:00', '10:00-11:00']
        picked_slots = request.POST.getlist('time_slots')
        # clear their old slots first, then save the new set fresh
        DoctorAvailability.objects.filter(doctor=doctor).delete()
        for slot in picked_slots:
            DoctorAvailability.objects.create(doctor=doctor, time_slot=slot)
        messages.success(request, 'Your available time slots have been updated.')
        return redirect('doctor_settings')

    # this doctor's currently saved slots, so the template can show them pre-ticked
    saved_slots = list(DoctorAvailability.objects.filter(doctor=doctor).values_list('time_slot', flat=True))
    return render(request, 'dashboard/appointment_management/doctor_settings.html', {
        'time_slot_choices': Appointment.TIME_SLOT_CHOICES,
        'saved_slots': saved_slots,
    })


# lists appointments for staff: doctors see only their own, everyone else sees all
@login_required
@required_role(['admin', 'doctor', 'nurse', 'receptionist'], 'You do not have permission to view appointments.')
def appointment_index(request):
    # doctors only see the appointments assigned to them; other staff see every appointment
    if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
        appointments = Appointment.objects.filter(doctor=request.user)
    else:
        appointments = Appointment.objects.all()
    return render(request, 'dashboard/appointment_management/index.html', {'appointments': appointments})


# shows one appointment's full details to staff
@login_required
@required_role(['admin', 'doctor', 'nurse', 'receptionist'], 'You do not have permission to view this appointment.')
def appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # find the appointment or show a 404 page
    doctor_room = _doctor_room(appointment.doctor)  # room number, shown alongside the doctor's name
    return render(request, 'dashboard/appointment_management/view.html', {
        'appointment': appointment,
        'doctor_room': doctor_room,
    })


# lets staff register an appointment on a patient's behalf (e.g. phone or walk-in booking)
@login_required
@required_role(['admin', 'doctor', 'nurse', 'receptionist'], 'You do not have permission to add appointments.')
def appointment_add(request):
    appointment = Appointment(status='pending')  # a blank appointment, only used so the template can show default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = StaffAppointmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # appointments registered from the dashboard are always paid in cash at the hospital;
        # this checkbox just says whether the cash was already handed over
        cash_received = request.POST.get('cash_received') == 'yes'

        # the patient details fields, already trimmed (and the NIC upper-cased) by the form's checks
        patient_name = form.cleaned_data['patient_name']
        patient_contact = form.cleaned_data['patient_contact']
        # find this caller's existing patient account by phone number, or make a new one
        patient_user = _find_or_create_call_in_patient(patient_name, patient_contact)

        appointment.patient = patient_user
        appointment.department = request.POST.get('department', '')
        appointment.date = request.POST.get('date', '')
        appointment.time_slot = request.POST.get('time_slot', '')
        appointment.doctor_id = request.POST.get('doctor') or None
        appointment.message = request.POST.get('message', '')
        appointment.status = request.POST.get('status', 'pending')
        appointment.patient_name = patient_name
        appointment.patient_contact = patient_contact
        appointment.patient_age = form.cleaned_data['patient_age']
        appointment.patient_address = form.cleaned_data['patient_address']
        appointment.patient_nic = form.cleaned_data['patient_nic']
        appointment.save()
        if appointment.doctor:
            send_doctor_assignment_email(appointment)  # let the doctor know they have a new appointment
        _create_appointment_payment_record(appointment, 'cash', paid_now=cash_received)
        messages.success(request, 'Appointment has been registered.')
        return redirect('appointment_index')

    # every active doctor, so the page can build the doctor dropdown - their department and
    # available time slots are loaded here too, so the page can filter the Doctor dropdown by
    # department and the Time Slot dropdown by the picked doctor's own availability
    doctors = User.objects.filter(
        profile__role='doctor', is_active=True
    ).select_related('staff_profile').prefetch_related('available_slots').order_by('first_name', 'last_name')
    return render(request, 'dashboard/appointment_management/add.html', {
        'form': form, 'appointment': appointment, 'doctors': doctors,
    })


# staff edit form for an appointment + its payment; routes the assigned doctor to the pharmacy app instead
@login_required
@required_role(['admin', 'doctor', 'nurse', 'receptionist'], 'You do not have permission to edit appointments.')
def appointment_edit(request, pk):
    # the doctor assigned to this appointment gets a read-only details view plus
    # a pharmacy section to prescribe medicine (handled by the pharmacy app).
    # everyone else (reception/admin) gets the full edit form, unchanged.
    appointment = get_object_or_404(Appointment, pk=pk)

    if appointment.doctor == request.user:
        return prescribe_medicine_for_appointment(request, appointment)

    # remember this here, before the form below touches the appointment object.
    # form.is_valid() fills appointment.status with the posted value as a side
    # effect, so checking status after that point would always see the new value
    was_confirmed = appointment.status == 'confirmed'
    was_cancelled = appointment.status == 'cancelled'  # remembered for the same reason as was_confirmed above
    previous_doctor_id = appointment.doctor_id  # remembered so we can tell if the doctor changes below

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
        payment.amount = Decimal(request.POST.get('payment-amount') or 0)  # decimal, so it can be subtracted later
        payment.method = request.POST.get('payment-method', 'cash')
        payment.status = request.POST.get('payment-status', 'pending')
        if payment.status == 'paid' and not payment.paid_at:
            payment.paid_at = timezone.now()  # stamp the first time it's marked paid
        payment.save()

        if appointment.status == 'confirmed' and not was_confirmed:
            # status just changed to confirmed here, so let the patient know by email
            send_appointment_confirmation_email(appointment)
        elif appointment.status == 'cancelled' and not was_cancelled:
            # status just changed to cancelled here, so let the patient know by email
            send_appointment_cancellation_email(appointment)

        if appointment.doctor_id and appointment.doctor_id != previous_doctor_id:
            # a doctor was just assigned or changed here, so let the doctor know by email
            send_doctor_assignment_email(appointment)

        messages.success(request, 'Appointment has been updated.')
        return redirect('appointment_view', pk=appointment.pk)

    # every active patient/doctor, so the page can build the patient and doctor dropdowns
    patients = User.objects.filter(profile__role='patient', is_active=True).order_by('first_name', 'last_name')
    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')
    return render(request, 'dashboard/appointment_management/edit.html', {
        'form': form, 'payment_form': payment_form, 'appointment': appointment, 'payment': payment,
        'patients': patients, 'doctors': doctors, 'is_doctor_view': False,
    })


# deletes an appointment; only actually deletes on a POST (confirm button), not a plain page visit
@login_required
@required_role(['admin', 'receptionist'], 'You do not have permission to delete appointments.')
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)  # find the appointment or show a 404 page
    if request.method == 'POST':
        # only delete when the confirm form is submitted, not on a plain page visit
        appointment.delete()
        messages.success(request, 'The appointment has been deleted.')
        return redirect('appointment_index')
    # not a POST request, so just go back to the list without deleting anything
    return redirect('appointment_index')


# lets a receptionist mark a pending cash consultation payment as received
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


# lets staff view and update the consultation fee charged for each department
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


# lets staff view every consultation payment, with a search box and status filter
@login_required
@required_role(['admin', 'receptionist'], 'You do not have permission to view payments.')
def payment_index(request):
    search_query = request.GET.get('q', '')  # patient name or transaction ref typed in the search box
    status_filter = request.GET.get('status', '')  # payment status picked in the dropdown

    # every payment, newest first, with the appointment/patient/doctor loaded in the same query
    payments = Payment.objects.select_related(
        'appointment', 'appointment__patient', 'appointment__doctor'
    ).order_by('-created_at')

    if search_query:
        # match either the patient's name or the payment's transaction reference
        payments = payments.filter(
            Q(appointment__patient_name__icontains=search_query) |
            Q(transaction_ref__icontains=search_query)
        )
    if status_filter:
        payments = payments.filter(status=status_filter)

    # split the payment list into pages of 15, so it never grows too long
    paginator = Paginator(payments, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/payment_management/index.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Payment.STATUS_CHOICES,
    })


# lets staff refund a paid consultation payment (e.g. a phone-cancelled booking); also cancels the appointment
@login_required
@required_role(['admin', 'receptionist'], 'You do not have permission to refund payments.')
def payment_refund(request, pk):
    payment = get_object_or_404(Payment, pk=pk)  # find the payment or show a 404 page

    if request.method == 'POST' and payment.status == 'paid':
        payment.status = 'refunded'  # mark the money as given back
        payment.save()
        payment.appointment.status = 'cancelled'  # the appointment no longer stands once refunded
        payment.appointment.save()
        send_appointment_refund_email(payment.appointment)  # let the patient know their appointment was cancelled and refunded
        messages.success(request, 'Payment has been refunded and the appointment cancelled.')
    else:
        messages.error(request, 'This payment cannot be refunded right now.')

    return redirect('payment_index')


# ── Frontend ───────────────────────────────────────────────────────────────

# public booking form: anyone can view and fill this page, no login needed
def appointment_form(request):
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

            if appointment.doctor:
                send_doctor_assignment_email(appointment)  # let the doctor know they have a new appointment

            _create_appointment_payment_record(appointment, payment_method)

            if payment_method == 'online':
                messages.success(request, 'Payment received. Your appointment is confirmed!')
            else:
                send_email_appointment_without_payment(appointment)
                messages.success(request, 'Appointment booked. Please pay at the hospital reception to confirm it.')
            return redirect('appointment_form')

    # fee for every department, shown on the payment step of the form
    fees = {row.department: str(row.fee) for row in DepartmentFee.objects.all()}
    # every active doctor, so the page can build the doctor dropdown
    # select_related('staff_profile') avoids one extra query per doctor below
    doctors = User.objects.filter(profile__role='doctor', is_active=True).select_related('staff_profile').order_by('first_name', 'last_name')
    # each doctor's own hourly fee, added on top of the department fee on the payment step
    doctor_fees = {str(doctor.pk): str(_doctor_fee(doctor)) for doctor in doctors}
    # department each doctor belongs to, so the page can hide doctors from other departments
    doctor_departments = {str(doctor.pk): _doctor_department(doctor) for doctor in doctors}
    # each doctor's own saved time slots, so the page can hide slots this doctor doesn't work.
    # a doctor with no saved slots yet has not configured Doctor Settings, so treat them as
    # available in every slot rather than hiding all of them
    all_slot_values = [value for value, _label in Appointment.TIME_SLOT_CHOICES if value]
    doctor_slots = {}
    for doctor in doctors:
        saved_slots = list(doctor.available_slots.values_list('time_slot', flat=True))
        doctor_slots[str(doctor.pk)] = saved_slots if saved_slots else all_slot_values
    # doctor picked on the "Find a Doctor" page, so the dropdown here starts pre-selected on them
    selected_doctor_id = request.GET.get('doctor')
    return render(request, 'frontend/appointment/form.html', {
        'form': form, 'appointment': appointment, 'fees': fees, 'doctors': doctors, 'doctor_fees': doctor_fees,
        'doctor_departments': doctor_departments, 'doctor_slots': doctor_slots, 'selected_doctor_id': selected_doctor_id,
    })


# patient's "My Appointments" page: their own appointment list plus prescribed medicine, if any
@login_required
def my_appointments(request, pk=None):
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


# patient's "Payment History" page: every consultation payment and medicine payment for their own appointments
@login_required
def payment_history(request):
    # every consultation payment for this patient's own appointments, newest first
    consultation_payments = Payment.objects.filter(
        appointment__patient=request.user
    ).select_related('appointment').order_by('-created_at')

    # every medicine payment for this patient's own appointments, newest first
    medicine_payments = PharmacyOrder.objects.filter(
        appointment__patient=request.user
    ).select_related('appointment').order_by('-created_at')

    return render(request, 'frontend/payment/history.html', {
        'consultation_payments': consultation_payments,
        'medicine_payments': medicine_payments,
    })


# lets a patient download a pdf bill for the consultation fee they already paid
@login_required
def download_appointment_bill(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)  # 404 if this isn't their own appointment
    payment = getattr(appointment, 'payment', None)  # the payment linked to this appointment, if any

    if not payment or payment.status != 'paid':
        # nothing paid yet, so there is no bill to give out
        messages.error(request, 'This appointment has no paid bill yet.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    amount_before_discount = payment.amount + payment.discount_amount  # add the discount back to see the original total
    department_fee = amount_before_discount - payment.doctor_fee_amount  # hospital's own base charge, doctor's cut taken out
    doctor_fee = payment.doctor_fee_amount  # the doctor's own cut, snapshotted at payment time

    from xhtml2pdf import pisa  # html to pdf library, only needed here so it is imported at this point
    html = render_to_string('frontend/appointment/appointment_bill_pdf.html', {
        'appointment': appointment,
        'payment': payment,
        'department_fee': department_fee,
        'doctor_fee': doctor_fee,
        'discount_amount': payment.discount_amount,
    })
    response = HttpResponse(content_type='application/pdf')  # tell the browser this is a pdf file
    response['Content-Disposition'] = f'attachment; filename="bill_{payment.transaction_ref}.pdf"'  # force a download prompt
    pisa.CreatePDF(html, dest=response)  # turn the html into a pdf and write it into the response
    return response


# lets a patient reschedule the date and time of their own appointment
@login_required
def edit_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    # form is only used to check the new date/time slot are valid; the actual save is done by hand below
    form = AppointmentEditForm(request.POST or None, instance=appointment)

    # if the form is invalid, this whole block is skipped and we fall through to the render
    # below, which shows the page again with the error messages
    if request.method == 'POST' and form.is_valid():
        appointment.date = request.POST.get('date', '')
        appointment.time_slot = request.POST.get('time_slot', '')
        appointment.save()
        send_appointment_update_email(appointment)  # let the patient know their appointment details have changed
        messages.success(request, 'Appointment updated successfully.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    return render(request, 'frontend/appointment/edit_appointment.html', {
        'form': form, 'appointment': appointment,
    })


# lets a patient cancel their own appointment, but only more than 24 hours before it starts
@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)

    if request.method != 'POST':
        # this action only makes sense as a button click, not a page visit
        return redirect('my_appointment_detail', pk=appointment.pk)

    if appointment.status == 'cancelled':
        # already cancelled, nothing to do - stops a double click from causing confusion
        messages.error(request, 'This appointment is already cancelled.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    start_datetime = _appointment_start_datetime(appointment)  # when the appointment actually starts
    if start_datetime - timezone.now() < timedelta(hours=24):
        # too close to the appointment time - block the cancel with a clear message
        messages.error(request, "You can't cancel within 24 hours of your appointment.")
        return redirect('my_appointment_detail', pk=appointment.pk)

    payment = getattr(appointment, 'payment', None)  # the payment linked to this appointment, if any

    if payment and payment.method == 'online' and payment.status == 'paid':
        # money was paid online - send them to the refund page instead of cancelling right away
        return redirect('refund_appointment', pk=appointment.pk)

    # cash payment (paid or still pending) or no payment at all - cancel straight away
    appointment.status = 'cancelled'
    appointment.save()
    send_appointment_cancellation_email(appointment)  # let the patient know their appointment was cancelled
    messages.success(request, 'Your appointment has been cancelled.')
    return redirect('my_appointment_detail', pk=appointment.pk)


# shows the demo refund confirmation page for an online-paid appointment the patient is cancelling
@login_required
def refund_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)
    payment = getattr(appointment, 'payment', None)  # the payment linked to this appointment, if any

    # guard against someone opening this link directly when it no longer applies
    already_cancelled = appointment.status == 'cancelled'
    not_online_paid = not (payment and payment.method == 'online' and payment.status == 'paid')
    too_late = _appointment_start_datetime(appointment) - timezone.now() < timedelta(hours=24)

    if already_cancelled or not_online_paid or too_late:
        messages.error(request, 'This appointment cannot be refunded right now.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    return render(request, 'frontend/appointment/refund_appointment.html', {
        'appointment': appointment,
        'payment': payment,
    })


# finishes the refund a patient confirmed on the refund page: marks the payment refunded and the appointment cancelled
@login_required
def appointment_refund_process_by_patient(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, patient=request.user)

    if request.method != 'POST':
        # this action only makes sense as a button click, not a page visit
        return redirect('refund_appointment', pk=appointment.pk)

    payment = getattr(appointment, 'payment', None)  # the payment linked to this appointment, if any

    # re-check everything again, in case time passed since the refund page was opened
    already_cancelled = appointment.status == 'cancelled'
    not_online_paid = not (payment and payment.method == 'online' and payment.status == 'paid')
    too_late = _appointment_start_datetime(appointment) - timezone.now() < timedelta(hours=24)

    if already_cancelled or not_online_paid or too_late:
        messages.error(request, 'This appointment cannot be refunded right now.')
        return redirect('my_appointment_detail', pk=appointment.pk)

    appointment.status = 'cancelled'
    appointment.save()
    payment.status = 'refunded'
    payment.save()
    send_appointment_refund_email(appointment)  # let the patient know their appointment was cancelled and refunded
    messages.success(request, 'Your appointment has been cancelled and the refund has been processed.')
    return redirect('my_appointment_detail', pk=appointment.pk)
