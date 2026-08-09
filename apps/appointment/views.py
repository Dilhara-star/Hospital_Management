from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator  # splits a long medicine list into pages
from django.db import transaction  # keeps stock updates safe when two requests happen at the same time
from django.db.models import F  # lets us update a number based on its own current value in the database
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string  # turns a template into an HTML string, used for PDFs
from django.http import HttpResponse
from django.utils import timezone  # used to stamp when a payment was paid
from xhtml2pdf import pisa  # turns an HTML string into a PDF file
from .models import Appointment, DepartmentFee, Payment, PrescriptionItem, PharmacyOrder
from .forms import AppointmentForm, StaffAppointmentForm, PaymentForm
from .notifications import send_appointment_confirmation_email  # emails the patient once an appointment is confirmed
from apps.inventory.models import Medicine, MedicineStock  # the pharmacy catalog the doctor picks medicine from
from apps.user_management.models import StaffProfile  # holds the room number and hourly fee for a doctor

# roles allowed to manage fees and confirm cash payments
PAYMENT_STAFF_ROLES = ('admin', 'receptionist')

# roles allowed to run the pharmacy counter (view prescriptions, dispense, take payment)
PHARMACY_STAFF_ROLES = ('admin', 'pharmacist')

# roles allowed to view reports (this first version only has doctor reports)
REPORT_STAFF_ROLES = ('admin', 'doctor')


def _is_payment_staff(user):
    # true only for logged in users whose profile role can handle payments
    return hasattr(user, 'profile') and user.profile.role in PAYMENT_STAFF_ROLES


def _is_pharmacist(user):
    # true only for logged in users whose profile role can run the pharmacy counter
    return hasattr(user, 'profile') and user.profile.role in PHARMACY_STAFF_ROLES


def _doctor_room(doctor):
    # the room number the receptionist assigned to this doctor, or '' if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return ''
    try:
        return doctor.profile.staff_profile.room_number
    except StaffProfile.DoesNotExist:
        return ''


def _doctor_fee(doctor):
    # this doctor's own consultation fee, or 0 if none has been set yet
    if not doctor or not hasattr(doctor, 'profile'):
        return 0
    try:
        return doctor.profile.staff_profile.hourly_fee
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
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                # we cannot save a booking without a logged in user, so ask them to log in
                messages.error(request, 'Please log in or sign up to complete your booking.')
            else:
                # 'online' or 'cash', chosen on the payment step of the form
                payment_method = request.POST.get('payment_method', 'cash')

                appointment = form.save(commit=False)  # build the appointment but don't save yet
                appointment.patient = request.user  # attach the logged in user as the patient
                appointment.save()  # save the appointment so it has an id

                _record_payment(appointment, payment_method)

                if payment_method == 'online':
                    messages.success(request, 'Payment received. Your appointment is confirmed!')
                else:
                    messages.success(request, 'Appointment booked. Please pay at the hospital reception to confirm it.')
                return redirect('appointment_form')
    else:
        initial = {}
        if request.user.is_authenticated:
            # fill the name field with the logged in user's name, to save typing
            initial['patient_name'] = request.user.get_full_name()
        form = AppointmentForm(initial=initial)

    # fee for every department, shown on the payment step of the form
    fees = {row.department: str(row.fee) for row in DepartmentFee.objects.all()}
    # each doctor's own hourly fee, added on top of the department fee on the payment step
    doctors = User.objects.filter(profile__role='doctor', is_active=True)
    doctor_fees = {str(doctor.pk): str(_doctor_fee(doctor)) for doctor in doctors}
    return render(request, 'frontend/appointment/form.html', {'form': form, 'fees': fees, 'doctor_fees': doctor_fees})

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
    appointment = Appointment.objects.get(pk=pk)
    doctor_room = _doctor_room(appointment.doctor)  # room number, shown alongside the doctor's name
    return render(request, 'dashboard/appointment_management/view.html', {
        'appointment': appointment,
        'doctor_room': doctor_room,
    })


@login_required
def appointment_add(request):
    # lets staff register an appointment on a patient's behalf (e.g. phone or walk-in booking)
    if request.method == 'POST':
        form = StaffAppointmentForm(request.POST)
        if form.is_valid():
            # appointments registered from the dashboard are always paid in cash at the hospital;
            # this checkbox just says whether the cash was already handed over
            cash_received = request.POST.get('cash_received') == 'yes'
            appointment = form.save()  # patient, status, etc. all come from the form
            _record_payment(appointment, 'cash', paid_now=cash_received)
            messages.success(request, 'Appointment has been registered.')
            return redirect('appointment_index')
    else:
        form = StaffAppointmentForm(initial={'status': 'pending'})
    return render(request, 'dashboard/appointment_management/add.html', {'form': form})


@login_required
def appointment_edit(request, pk):
    # the doctor assigned to this appointment gets a read-only details view plus
    # a pharmacy section to prescribe medicine. everyone else (reception/admin)
    # gets the full edit form, unchanged.
    appointment = Appointment.objects.get(pk=pk)

    if appointment.doctor == request.user:
        return _prescribe_medicine(request, appointment)

    payment = getattr(appointment, 'payment', None)  # may be missing for old appointments

    # a prefix keeps this form's "status" field from clashing with the appointment form's own "status" field
    if request.method == 'POST':
        form = StaffAppointmentForm(request.POST, instance=appointment)
        payment_form = PaymentForm(request.POST, instance=payment, prefix='payment')
        if form.is_valid() and payment_form.is_valid():
            form.save()

            new_payment = payment_form.save(commit=False)
            new_payment.appointment = appointment  # needed the first time, if there was no payment yet
            if new_payment.status == 'paid' and not new_payment.paid_at:
                new_payment.paid_at = timezone.now()  # stamp the first time it's marked paid
            new_payment.save()

            messages.success(request, 'Appointment has been updated.')
            return redirect('appointment_view', pk=appointment.pk)
    else:
        form = StaffAppointmentForm(instance=appointment)
        payment_form = PaymentForm(instance=payment, prefix='payment')

    return render(request, 'dashboard/appointment_management/edit.html', {
        'form': form, 'payment_form': payment_form, 'appointment': appointment, 'is_doctor_view': False,
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
        medicine = Medicine.objects.get(pk=request.POST.get('medicine_id'))  # the medicine the doctor picked
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
    appointment = Appointment.objects.get(pk=pk)  # which appointment the doctor is prescribing for
    medicines_page, search_query, category = _search_medicines(request)  # same filtering as the full page
    return render(request, 'dashboard/appointment_management/_pharmacy_list.html', {
        'appointment': appointment,
        'medicines': medicines_page,
        'search_query': search_query,
        'category': category,
    })


def appointment_delete(request, pk):
    appointment = Appointment.objects.get(pk=pk)
    appointment.delete()
    messages.success(request, 'Your appointment has been deleted.')
    return redirect('appointment_index')


@login_required
def prescription_item_delete(request, pk, item_pk):
    # lets the assigned doctor remove a medicine they added to this prescription by mistake
    appointment = Appointment.objects.get(pk=pk)

    if appointment.doctor != request.user:
        messages.error(request, 'You do not have permission to edit this prescription.')
        return redirect('appointment_index')

    if request.method == 'POST':
        item = PrescriptionItem.objects.get(pk=item_pk, appointment=appointment)  # must belong to this appointment
        item.delete()
        if _is_ajax(request):
            return _prescribed_items_response(request, appointment)  # just refresh the table, no page reload
        messages.success(request, 'Medicine removed from the prescription.')

    return redirect('appointment_edit', pk=appointment.pk)


@login_required
def confirm_cash_payment(request, pk):
    # only reception/admin staff may confirm that cash was received
    if not _is_payment_staff(request.user):
        messages.error(request, 'You do not have permission to confirm payments.')
        return redirect('appointment_index')

    appointment = Appointment.objects.get(pk=pk)
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
def fee_index(request):
    # only reception/admin staff may change consultation fees
    if not _is_payment_staff(request.user):
        messages.error(request, 'You do not have permission to manage fees.')
        return redirect('dashboard_index')

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
def pharmacy_queue(request):
    # only pharmacists/admin may see the pharmacy counter
    if not _is_pharmacist(request.user):
        messages.error(request, 'You do not have permission to view the pharmacy counter.')
        return redirect('dashboard_index')

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
def pharmacy_order_detail(request, pk):
    # only pharmacists/admin may open an order
    if not _is_pharmacist(request.user):
        messages.error(request, 'You do not have permission to view the pharmacy counter.')
        return redirect('dashboard_index')

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


# ── Reports ────────────────────────────────────────────────────────────────

def _is_report_staff(user):
    # true only for logged in users whose profile role may view reports
    return hasattr(user, 'profile') and user.profile.role in REPORT_STAFF_ROLES


def _require_report_staff(request):
    # only doctors and admins may open any report page.
    # returns a redirect when not allowed, or None when the view may continue.
    if not _is_report_staff(request.user):
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('dashboard_index')
    return None


def _resolve_report_doctor(request):
    # works out which doctor's report to show.
    # a doctor always sees their own report - the ?doctor_id= query string is
    # ignored so they can never view a colleague's report by editing the URL.
    # an admin may filter by any doctor; returns None until they pick one,
    # which the report pages use to show a doctor dropdown instead of data.
    if request.user.profile.role == 'doctor':
        return request.user

    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return None
    return get_object_or_404(User, pk=doctor_id, profile__role='doctor')


def _doctor_revenue_data(doctor, start_date, end_date):
    # every appointment for this doctor, with its payment attached, inside the chosen date range
    appointments = Appointment.objects.filter(doctor=doctor).select_related('patient', 'payment').order_by('-date')
    if start_date:
        appointments = appointments.filter(date__gte=start_date)
    if end_date:
        appointments = appointments.filter(date__lte=end_date)

    total_collected = 0  # everything the hospital collected for this doctor's appointments
    take_home = 0  # just the doctor's own cut of that money
    paid_count = 0

    for appointment in appointments:
        payment = getattr(appointment, 'payment', None)
        if payment and payment.status == 'paid':
            total_collected += payment.amount
            take_home += payment.doctor_fee_amount
            paid_count += 1

    return {
        'doctor': doctor,
        'appointments': appointments,
        'total_collected': total_collected,
        'take_home': take_home,
        'hospital_share': total_collected - take_home,
        'paid_count': paid_count,
    }


def _appointment_summary_data(doctor, start_date, end_date):
    # every appointment for this doctor, inside the chosen date range
    appointments = Appointment.objects.filter(doctor=doctor).select_related('patient').order_by('-date')
    if start_date:
        appointments = appointments.filter(date__gte=start_date)
    if end_date:
        appointments = appointments.filter(date__lte=end_date)

    return {
        'doctor': doctor,
        'appointments': appointments,
        'total_count': appointments.count(),
        'pending_count': appointments.filter(status='pending').count(),
        'confirmed_count': appointments.filter(status='confirmed').count(),
        'cancelled_count': appointments.filter(status='cancelled').count(),
    }


@login_required
def reports_index(request):
    # only doctors and admins may open the reports menu
    error_response = _require_report_staff(request)
    if error_response:
        return error_response

    return render(request, 'dashboard/report_management/index.html')


@login_required
def doctor_revenue_report(request):
    error_response = _require_report_staff(request)
    if error_response:
        return error_response

    doctor = _resolve_report_doctor(request)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    context = {'doctor': doctor, 'start_date': start_date, 'end_date': end_date}
    if doctor:
        context.update(_doctor_revenue_data(doctor, start_date, end_date))
    if request.user.profile.role == 'admin':
        # only admins get to filter by doctor, so only they need this dropdown list
        context['doctors'] = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    return render(request, 'dashboard/report_management/doctor_revenue.html', context)


@login_required
def doctor_revenue_report_pdf(request):
    error_response = _require_report_staff(request)
    if error_response:
        return error_response

    doctor = _resolve_report_doctor(request)
    if doctor is None:
        messages.error(request, 'Please choose a doctor first.')
        return redirect('doctor_revenue_report')

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    data = _doctor_revenue_data(doctor, start_date, end_date)
    data['start_date'] = start_date
    data['end_date'] = end_date

    html = render_to_string('dashboard/report_management/doctor_revenue_pdf.html', data)  # build the PDF's HTML
    response = HttpResponse(content_type='application/pdf')  # tell the browser this is a PDF file
    response['Content-Disposition'] = f'attachment; filename="doctor_revenue_{doctor.pk}.pdf"'  # forces a download
    pisa.CreatePDF(html, dest=response)  # turn the HTML into a PDF and write it into the response
    return response


@login_required
def appointment_summary_report(request):
    error_response = _require_report_staff(request)
    if error_response:
        return error_response

    doctor = _resolve_report_doctor(request)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    context = {'doctor': doctor, 'start_date': start_date, 'end_date': end_date}
    if doctor:
        context.update(_appointment_summary_data(doctor, start_date, end_date))
    if request.user.profile.role == 'admin':
        context['doctors'] = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    return render(request, 'dashboard/report_management/appointment_summary.html', context)


@login_required
def appointment_summary_report_pdf(request):
    error_response = _require_report_staff(request)
    if error_response:
        return error_response

    doctor = _resolve_report_doctor(request)
    if doctor is None:
        messages.error(request, 'Please choose a doctor first.')
        return redirect('appointment_summary_report')

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    data = _appointment_summary_data(doctor, start_date, end_date)
    data['start_date'] = start_date
    data['end_date'] = end_date

    html = render_to_string('dashboard/report_management/appointment_summary_pdf.html', data)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="appointment_summary_{doctor.pk}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response