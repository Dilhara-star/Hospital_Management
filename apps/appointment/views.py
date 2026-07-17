from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone  # used to stamp when a payment was paid
from .models import Appointment, DepartmentFee, Payment, PrescriptionItem
from .forms import AppointmentForm, StaffAppointmentForm, PaymentForm
from apps.inventory.models import Medicine  # the pharmacy catalog the doctor picks medicine from

# roles allowed to manage fees and confirm cash payments
PAYMENT_STAFF_ROLES = ('admin', 'receptionist')


def _is_payment_staff(user):
    # true only for logged in users whose profile role can handle payments
    return hasattr(user, 'profile') and user.profile.role in PAYMENT_STAFF_ROLES


def _record_payment(appointment, payment_method, paid_now=False):
    # shared by the patient booking form and the staff "Add Appointment" page.
    # paid_now covers cash that's handed over right at the reception desk.
    if payment_method == 'online':
        paid_now = True  # online payments are always paid immediately

    # look up the fee for this department, default to 0 if staff haven't set one yet
    fee_row = DepartmentFee.objects.filter(department=appointment.department).first()
    fee_amount = fee_row.fee if fee_row else 0

    if paid_now:
        appointment.status = 'confirmed'  # money is in, so confirm right away
        appointment.save()

    ref_prefix = 'PAY' if payment_method == 'online' else 'CASH'  # demo receipt number style
    Payment.objects.create(
        appointment=appointment,  # link the payment to this appointment
        amount=fee_amount,  # the department's consultation fee
        method=payment_method,  # 'online' or 'cash'
        status='paid' if paid_now else 'pending',
        paid_at=timezone.now() if paid_now else None,  # paid time, if any
        transaction_ref=f'{ref_prefix}-{appointment.pk:06d}' if paid_now else '',
    )


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
    return render(request, 'frontend/appointment/form.html', {'form': form, 'fees': fees})

def appointment_view(request, pk):
    appointment = Appointment.objects.get(pk=pk)
    print(appointment)
    return render(request, 'dashboard/appointment_management/view.html', {'appointment': appointment})


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
        messages.success(request, f'{medicine.name} added to the prescription.')
        return redirect('appointment_edit', pk=appointment.pk)

    # search box and category dropdown on the pharmacy section, both optional
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    medicines = Medicine.objects.all()  # start from the full catalog, same one /inventory/medicines/ shows
    if search_query:
        medicines = medicines.filter(name__icontains=search_query)  # keep only names containing the search text
    if category:
        medicines = medicines.filter(category=category)  # keep only the chosen category

    # medicines already prescribed for this visit, oldest pick first
    prescribed_items = appointment.prescription_items.select_related('medicine').all()

    return render(request, 'dashboard/appointment_management/edit.html', {
        'appointment': appointment,
        'is_doctor_view': True,
        'medicines': medicines,
        'prescribed_items': prescribed_items,
        'search_query': search_query,
        'category': category,
        'category_choices': Medicine.CATEGORY_CHOICES,
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