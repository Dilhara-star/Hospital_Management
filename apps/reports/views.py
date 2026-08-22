from datetime import date, timedelta  # date tools used by the medicine expiry report
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.core.paginator import Paginator  # splits a long list of appointments into pages
from django.db.models import Sum, Count, F, Q  # aggregation and search tools used across the reports
from django.shortcuts import get_object_or_404, redirect, render
from apps.appointment.models import Appointment, DepartmentFee, Payment  # the rows reports are built from
from apps.pharmacy.models import PharmacyOrder, PrescriptionItem  # the medicine orders and prescribed items reports are built from
from apps.stock.models import Medicine, MedicineStock  # the medicine catalog and stock batches reports are built from
from apps.supplier.models import Supplier  # supplier records used by the purchase report
from apps.user_management.models import PatientProfile, StaffProfile, UserProfile  # the patient and staff records reports are built from
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role
from apps.reports.utils import export_pdf  # shared helper that turns a report into a downloadable pdf


# shows the reports landing page with links to every report below
@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def reports_index(request):
    return render(request, 'dashboard/report_management/index.html')


# shows how much money one doctor's appointments have collected, and their own cut of it
@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def doctor_revenue_report(request):
    if request.user.profile.role == 'doctor':
        # a doctor always sees their own report - ignore ?doctor_id= in the
        # URL so they can never view a colleague's report by editing it
        doctor = request.user
    else:
        # an admin may filter by any doctor; None until they pick one, which
        # the template uses to show a doctor dropdown instead of data
        doctor_id = request.GET.get('doctor_id')
        doctor = get_object_or_404(User, pk=doctor_id, profile__role='doctor') if doctor_id else None

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    context = {'doctor': doctor, 'start_date': start_date, 'end_date': end_date}

    if doctor:
        # every appointment for this doctor, with its payment attached, inside the chosen date range
        appointments = Appointment.objects.filter(doctor=doctor).select_related('patient', 'payment').order_by('-date')
        if start_date:
            appointments = appointments.filter(date__gte=start_date)
        if end_date:
            appointments = appointments.filter(date__lte=end_date)

        total_collected = 0  # everything the hospital collected for this doctor's appointments
        take_home = 0  # just the doctor's own cut of that money
        for appointment in appointments:
            payment = getattr(appointment, 'payment', None)
            if payment and payment.status == 'paid':
                total_collected += payment.amount
                take_home += payment.doctor_fee_amount

        context['appointments'] = appointments
        context['total_collected'] = total_collected
        context['take_home'] = take_home
        context['hospital_share'] = total_collected - take_home

    if request.user.profile.role == 'admin':
        # only admins get to filter by doctor, so only they need this dropdown list
        context['doctors'] = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    if request.GET.get('download') == 'pdf':
        # can't build a PDF without knowing which doctor, so send them back with an error
        if doctor is None:
            messages.error(request, 'Please choose a doctor first.')
            return redirect('doctor_revenue_report')

        pdf_response = export_pdf(request, 'dashboard/report_management/doctor_revenue_pdf.html', context, f'doctor_revenue_{doctor.pk}.pdf')  # build the pdf, or None if not asked for
        if pdf_response:
            return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/doctor_revenue.html', context)


# shows one doctor's appointment counts broken down by status (pending/confirmed/cancelled)
@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def appointment_summary_report(request):
    if request.user.profile.role == 'doctor':
        # a doctor always sees their own report - ignore ?doctor_id= in the
        # URL so they can never view a colleague's report by editing it
        doctor = request.user
    else:
        # an admin may filter by any doctor; None until they pick one, which
        # the template uses to show a doctor dropdown instead of data
        doctor_id = request.GET.get('doctor_id')
        doctor = get_object_or_404(User, pk=doctor_id, profile__role='doctor') if doctor_id else None

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    context = {'doctor': doctor, 'start_date': start_date, 'end_date': end_date}

    if doctor:
        # every appointment for this doctor, inside the chosen date range
        appointments = Appointment.objects.filter(doctor=doctor).select_related('patient').order_by('-date')
        if start_date:
            appointments = appointments.filter(date__gte=start_date)
        if end_date:
            appointments = appointments.filter(date__lte=end_date)

        context['appointments'] = appointments
        context['total_count'] = appointments.count()
        context['pending_count'] = appointments.filter(status='pending').count()
        context['confirmed_count'] = appointments.filter(status='confirmed').count()
        context['cancelled_count'] = appointments.filter(status='cancelled').count()

    if request.user.profile.role == 'admin':
        context['doctors'] = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    if request.GET.get('download') == 'pdf':
        # can't build a PDF without knowing which doctor, so send them back with an error
        if doctor is None:
            messages.error(request, 'Please choose a doctor first.')
            return redirect('appointment_summary_report')

        pdf_response = export_pdf(request, 'dashboard/report_management/appointment_summary_pdf.html', context, f'appointment_summary_{doctor.pk}.pdf')  # build the pdf, or None if not asked for
        if pdf_response:
            return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/appointment_summary.html', context)


# shows total money collected hospital-wide, split between consultations and pharmacy
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def hospital_revenue_report(request):
    # this report is hospital-wide, so only admin may open it (a doctor only ever sees their own money)
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    context = {'start_date': start_date, 'end_date': end_date}  # values the template needs to redraw the filter form

    # every appointment that has a payment row, so we can add up consultation money
    appointments = Appointment.objects.select_related('payment').all()
    if start_date:
        appointments = appointments.filter(date__gte=start_date)  # drop appointments before the "from" date
    if end_date:
        appointments = appointments.filter(date__lte=end_date)  # drop appointments after the "to" date

    consultation_paid = 0  # consultation money already collected
    consultation_online = 0  # of that, how much came in through online payment
    consultation_cash = 0  # of that, how much came in as cash at the hospital
    consultation_pending = 0  # consultation money still owed
    consultation_refunded = 0  # consultation money paid back to patients

    for appointment in appointments:
        payment = getattr(appointment, 'payment', None)  # this appointment's payment row, or None if it has none yet
        if not payment:
            continue  # nothing to count without a payment row
        if payment.status == 'paid':
            consultation_paid += payment.amount  # add to the paid total
            if payment.method == 'online':
                consultation_online += payment.amount  # also add to the online total
            else:
                consultation_cash += payment.amount  # also add to the cash total
        elif payment.status == 'pending':
            consultation_pending += payment.amount  # still waiting to be collected
        elif payment.status == 'refunded':
            consultation_refunded += payment.amount  # was paid, then given back

    # every pharmacy order, so we can add up medicine money in the same date range
    pharmacy_orders = PharmacyOrder.objects.select_related('appointment')
    if start_date:
        pharmacy_orders = pharmacy_orders.filter(appointment__date__gte=start_date)  # same "from" date, on the linked appointment
    if end_date:
        pharmacy_orders = pharmacy_orders.filter(appointment__date__lte=end_date)  # same "to" date, on the linked appointment

    pharmacy_paid = 0  # medicine money already collected
    pharmacy_online = 0  # of that, how much came in through online payment
    pharmacy_cash = 0  # of that, how much came in as cash to the pharmacist
    pharmacy_pending = 0  # medicine money still owed

    for order in pharmacy_orders:
        if order.payment_status == 'paid':
            pharmacy_paid += order.total_amount  # add to the paid total
            if order.payment_method == 'online':
                pharmacy_online += order.total_amount  # also add to the online total
            else:
                pharmacy_cash += order.total_amount  # also add to the cash total
        else:
            pharmacy_pending += order.total_amount  # still waiting to be collected (0 if not dispensed yet)

    # fill in everything the template and the PDF both need
    context['consultation_paid'] = consultation_paid
    context['consultation_online'] = consultation_online
    context['consultation_cash'] = consultation_cash
    context['consultation_pending'] = consultation_pending
    context['consultation_refunded'] = consultation_refunded
    context['pharmacy_paid'] = pharmacy_paid
    context['pharmacy_online'] = pharmacy_online
    context['pharmacy_cash'] = pharmacy_cash
    context['pharmacy_pending'] = pharmacy_pending
    context['grand_total'] = consultation_paid + pharmacy_paid  # everything the hospital has actually collected

    pdf_response = export_pdf(request, 'dashboard/report_management/hospital_revenue_pdf.html', context, 'hospital_revenue.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/hospital_revenue.html', context)


# shows appointment count and paid revenue per department, side by side
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def department_performance_report(request):
    # hospital-wide across every department, so only admin may open it
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form

    appointments = Appointment.objects.select_related('payment').all()  # every appointment, with its payment attached
    if start_date:
        appointments = appointments.filter(date__gte=start_date)  # drop appointments before the "from" date
    if end_date:
        appointments = appointments.filter(date__lte=end_date)  # drop appointments after the "to" date

    # one fee row per department, looked up once and kept in a dict so we don't query it again per department
    fees_by_department = {fee.department: fee.fee for fee in DepartmentFee.objects.all()}

    # one counter dict per real department (skip the blank "Select Department" choice)
    department_stats = {}
    for code, label in Appointment.DEPARTMENT_CHOICES:
        if not code:
            continue  # this is the blank placeholder choice, not a real department
        department_stats[code] = {
            'label': label,  # the readable department name, e.g. "Cardiology"
            'fee': fees_by_department.get(code, 0),  # the department's base consultation fee
            'appointment_count': 0,  # how many appointments this department had, filled in below
            'paid_revenue': 0,  # how much money was collected for this department, filled in below
        }

    # walk the appointments once and add each one to its own department's counters
    for appointment in appointments:
        stats = department_stats.get(appointment.department)
        if not stats:
            continue  # appointment was saved with a blank/unknown department, skip it
        stats['appointment_count'] += 1  # one more appointment for this department
        payment = getattr(appointment, 'payment', None)  # this appointment's payment row, or None
        if payment and payment.status == 'paid':
            stats['paid_revenue'] += payment.amount  # add the paid amount to this department's revenue

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'department_stats': department_stats.values(),  # the finished list, one row per department
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/department_performance_pdf.html', context, 'department_performance.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/department_performance.html', context)


# ranks every doctor by revenue collected and take-home pay, highest first
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def doctors_leaderboard_report(request):
    # compares every doctor side by side, so only admin may open it
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form

    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')  # every active doctor

    appointments = Appointment.objects.filter(doctor__isnull=False).select_related('payment')  # only appointments that have a doctor
    if start_date:
        appointments = appointments.filter(date__gte=start_date)  # drop appointments before the "from" date
    if end_date:
        appointments = appointments.filter(date__lte=end_date)  # drop appointments after the "to" date

    # one counter dict per doctor, keyed by their id, so the loop below can find the right one fast
    stats_by_doctor = {}
    for doctor in doctors:
        stats_by_doctor[doctor.pk] = {
            'doctor': doctor,  # the doctor this row is about
            'appointment_count': 0,  # how many appointments they had, filled in below
            'paid_total': 0,  # total money collected for their appointments, filled in below
            'take_home': 0,  # of that, how much is the doctor's own cut, filled in below
        }

    # walk the appointments once and add each one to its own doctor's counters
    for appointment in appointments:
        stats = stats_by_doctor.get(appointment.doctor_id)
        if not stats:
            continue  # doctor is inactive or no longer has the doctor role, skip
        stats['appointment_count'] += 1  # one more appointment for this doctor
        payment = getattr(appointment, 'payment', None)  # this appointment's payment row, or None
        if payment and payment.status == 'paid':
            stats['paid_total'] += payment.amount  # add to the money collected for this doctor
            stats['take_home'] += payment.doctor_fee_amount  # add to the doctor's own cut

    leaderboard = list(stats_by_doctor.values())  # turn the dict into a plain list the template can loop over
    for row in leaderboard:
        row['hospital_share'] = row['paid_total'] - row['take_home']  # what's left after the doctor's own cut
    leaderboard.sort(key=lambda row: row['paid_total'], reverse=True)  # highest earning doctor first

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'leaderboard': leaderboard,
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/doctors_leaderboard_pdf.html', context, 'doctors_leaderboard.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/doctors_leaderboard.html', context)


# shows hospital-wide appointment status counts plus a filterable, paginated list
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def hospital_appointment_status_report(request):
    # hospital-wide across every doctor, so only admin may open it
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    department = request.GET.get('department', '')  # read the department chosen in the filter form, if any

    appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date')  # every appointment, newest first
    if start_date:
        appointments = appointments.filter(date__gte=start_date)  # drop appointments before the "from" date
    if end_date:
        appointments = appointments.filter(date__lte=end_date)  # drop appointments after the "to" date
    if department:
        appointments = appointments.filter(department=department)  # only this one department, if chosen

    # counts are worked out before the list is cut into pages, so they always cover the full filtered set
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'department': department,
        'departments': Appointment.DEPARTMENT_CHOICES,  # feeds the department drop-down in the filter form
        'total_count': appointments.count(),
        'pending_count': appointments.filter(status='pending').count(),
        'confirmed_count': appointments.filter(status='confirmed').count(),
        'cancelled_count': appointments.filter(status='cancelled').count(),
    }

    if request.GET.get('download') == 'pdf':
        # the PDF gets the full list, not just one page
        context['appointments'] = appointments
        pdf_response = export_pdf(request, 'dashboard/report_management/appointment_status_pdf.html', context, 'appointment_status.pdf')  # build the pdf, or None if not asked for
        if pdf_response:
            return pdf_response  # send the pdf back to the browser

    # the on-screen page shows 25 appointments at a time, so the list stays fast even with many rows
    paginator = Paginator(appointments, 25)  # split the queryset into pages of 25 rows each
    page_number = request.GET.get('page')  # which page the user asked for, from the URL
    context['page_obj'] = paginator.get_page(page_number)  # the one page of appointments to show right now

    return render(request, 'dashboard/report_management/appointment_status.html', context)


# shows every medicine whose total stock has fallen to or below its reorder level
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def low_stock_report(request):
    medicines = Medicine.objects.all().order_by('name')  # every medicine in the catalog, alphabetical
    # keep only the medicines that need reordering, using the model's own is_low_stock property
    low_stock_medicines = [medicine for medicine in medicines if medicine.is_low_stock]

    context = {'low_stock_medicines': low_stock_medicines}  # values the template and PDF both need

    pdf_response = export_pdf(request, 'dashboard/report_management/low_stock_pdf.html', context, 'low_stock.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/low_stock.html', context)


# shows stock batches that have already expired, or will expire within the next 30 days
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def medicine_expiry_report(request):
    cutoff_date = date.today() + timedelta(days=30)  # anything expiring on or before this date is worth showing

    # only batches that still have stock left, closest expiry first
    batches = MedicineStock.objects.select_related('medicine').filter(
        expiry_date__lte=cutoff_date, quantity__gt=0
    ).order_by('expiry_date')

    # split into two lists using the model's own is_expired property, so the template can show them separately
    expired_batches = [batch for batch in batches if batch.is_expired]
    expiring_soon_batches = [batch for batch in batches if not batch.is_expired]

    context = {
        'expired_batches': expired_batches,
        'expiring_soon_batches': expiring_soon_batches,
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/medicine_expiry_pdf.html', context, 'medicine_expiry.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/medicine_expiry.html', context)


# shows every medicine ranked by how many units were prescribed, with an estimated revenue
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def medicine_sales_report(request):
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    context = {'start_date': start_date, 'end_date': end_date}

    items = PrescriptionItem.objects.select_related('medicine')  # every prescribed medicine row
    if start_date:
        items = items.filter(created_at__date__gte=start_date)  # drop rows prescribed before the "from" date
    if end_date:
        items = items.filter(created_at__date__lte=end_date)  # drop rows prescribed after the "to" date

    # group the rows by medicine, adding up how many units and how many times each was prescribed
    sales_rows = items.values('medicine__id', 'medicine__name', 'medicine__price').annotate(
        total_quantity=Sum('quantity'),
        times_prescribed=Count('id'),
    ).order_by('-total_quantity')

    sales = []  # final list, one row per medicine, with its estimated revenue added in
    grand_total_revenue = 0  # estimated revenue across every medicine, at current catalog price
    for row in sales_rows:
        revenue = row['total_quantity'] * row['medicine__price']  # units sold x current price
        grand_total_revenue += revenue
        sales.append({
            'name': row['medicine__name'],
            'total_quantity': row['total_quantity'],
            'times_prescribed': row['times_prescribed'],
            'price': row['medicine__price'],
            'revenue': revenue,
        })

    context['sales'] = sales
    context['grand_total_revenue'] = grand_total_revenue

    pdf_response = export_pdf(request, 'dashboard/report_management/medicine_sales_pdf.html', context, 'medicine_sales.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/medicine_sales.html', context)


# shows how much money the current medicine stock is worth, per medicine and in total
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def stock_valuation_report(request):
    # only batches with a known purchase price add real value to the total
    batches = MedicineStock.objects.select_related('medicine').filter(purchase_price__isnull=False)

    # group the batches by medicine, adding up quantity and (quantity x purchase price) per medicine
    valuation_rows = batches.values('medicine__id', 'medicine__name').annotate(
        total_quantity=Sum('quantity'),
        total_value=Sum(F('quantity') * F('purchase_price')),
    ).order_by('-total_value')

    context = {
        'valuation_rows': valuation_rows,
        'grand_total_value': sum(row['total_value'] or 0 for row in valuation_rows),  # add up every medicine's value
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/stock_valuation_pdf.html', context, 'stock_valuation.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/stock_valuation.html', context)


# shows patients registered in a date range, plus active/inactive/discharged counts
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def patient_registration_report(request):
    # hospital-wide list of every patient, so only admin may open it
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form

    patients = PatientProfile.objects.select_related('user').order_by('-registered_date')  # every patient, newest first
    if start_date:
        patients = patients.filter(registered_date__gte=start_date)  # drop patients registered before the "from" date
    if end_date:
        patients = patients.filter(registered_date__lte=end_date)  # drop patients registered after the "to" date

    # counts are worked out before the list is cut into pages, so they always cover the full filtered set
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_count': patients.count(),
        'active_count': patients.filter(status='active').count(),
        'inactive_count': patients.filter(status='inactive').count(),
        'discharged_count': patients.filter(status='discharged').count(),
    }

    if request.GET.get('download') == 'pdf':
        # the PDF gets the full list, not just one page
        context['patients'] = patients
        pdf_response = export_pdf(request, 'dashboard/report_management/patient_registration_pdf.html', context, 'patient_registration.pdf')  # build the pdf, or None if not asked for
        if pdf_response:
            return pdf_response  # send the pdf back to the browser

    # the on-screen page shows 25 patients at a time, so the list stays fast even with many rows
    paginator = Paginator(patients, 25)  # split the queryset into pages of 25 rows each
    page_number = request.GET.get('page')  # which page the user asked for, from the URL
    context['page_obj'] = paginator.get_page(page_number)  # the one page of patients to show right now

    return render(request, 'dashboard/report_management/patient_registration.html', context)


# shows how many staff members work in each department, and how many hold each role
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def staff_headcount_report(request):
    # hospital-wide staff counts, so only admin may open it

    # every staff record grouped by department, busiest department first
    department_rows = StaffProfile.objects.exclude(department='').values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    department_labels = dict(StaffProfile.DEPARTMENT_CHOICES)  # turns 'cardiology' into 'Cardiology' for display
    department_stats = [
        {'label': department_labels.get(row['department'], row['department']), 'count': row['count']}
        for row in department_rows
    ]

    # every staff record grouped by role, most common role first
    role_rows = StaffProfile.objects.select_related('user__profile').values('user__profile__role').annotate(
        count=Count('id')
    ).order_by('-count')
    role_labels = dict(UserProfile.ROLE_CHOICES)  # turns 'doctor' into 'Doctor' for display
    role_stats = [
        {'label': role_labels.get(row['user__profile__role'], row['user__profile__role']), 'count': row['count']}
        for row in role_rows
    ]

    context = {
        'department_stats': department_stats,
        'role_stats': role_stats,
        'total_staff': StaffProfile.objects.count(),
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/staff_headcount_pdf.html', context, 'staff_headcount.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/staff_headcount.html', context)


# shows one patient's full history: appointments, prescribed medicines, and payments
@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def patient_medical_history_report(request):
    query = request.GET.get('q', '')  # the search text typed in the search box
    patient_id = request.GET.get('patient_id')  # which patient was picked from the search results

    if request.user.profile.role == 'doctor':
        # a doctor can only look up patients they have actually treated
        patients = PatientProfile.objects.filter(user__patient_appointments__doctor=request.user).distinct()
    else:
        # an admin can look up any patient in the system
        patients = PatientProfile.objects.all()

    if query:
        # match the search text against first name, last name, or mrn
        patients = patients.filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) | Q(mrn__icontains=query)
        )
    patients = patients.select_related('user').order_by('user__first_name', 'user__last_name')[:20]  # only show the first 20 matches

    context = {'query': query, 'patients': patients, 'patient': None}

    if patient_id:
        patient = get_object_or_404(PatientProfile, pk=patient_id)  # fetch the chosen patient, or 404 if the id is wrong

        if request.user.profile.role == 'doctor':
            # a doctor may only open a patient they have treated, even by typing the id directly in the url
            has_treated = Appointment.objects.filter(patient=patient.user, doctor=request.user).exists()
            if not has_treated:
                messages.error(request, 'You do not have permission to view this patient.')
                return redirect('patient_medical_history_report')

        # every appointment for this patient, newest first
        appointments = Appointment.objects.filter(patient=patient.user).select_related('doctor', 'payment').order_by('-date')
        if request.user.profile.role == 'doctor':
            # a doctor only sees the visits where they were the treating doctor
            appointments = appointments.filter(doctor=request.user)
        appointments = list(appointments)  # turn into a plain list so we can attach extra info to each row below

        # group the prescribed medicines by which appointment they belong to
        prescriptions_by_appointment = {}
        for item in PrescriptionItem.objects.filter(appointment__in=appointments).select_related('medicine'):
            prescriptions_by_appointment.setdefault(item.appointment_id, []).append(item)

        # group the pharmacy orders by which appointment they belong to
        orders_by_appointment = {}
        for order in PharmacyOrder.objects.filter(appointment__in=appointments):
            orders_by_appointment[order.appointment_id] = order

        for appointment in appointments:
            appointment.prescriptions = prescriptions_by_appointment.get(appointment.id, [])  # attach this visit's prescribed medicines
            appointment.pharmacy_order = orders_by_appointment.get(appointment.id)  # attach this visit's pharmacy order, or None

        context['patient'] = patient
        context['appointments'] = appointments

        if request.GET.get('download') == 'pdf':
            pdf_response = export_pdf(request, 'dashboard/report_management/patient_medical_history_pdf.html', context, f'patient_history_{patient.mrn}.pdf')  # build the pdf, or None if not asked for
            if pdf_response:
                return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/patient_medical_history.html', context)


# shows appointment count and paid revenue, grouped by day or by month
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def appointment_revenue_trend_report(request):
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    group_by = request.GET.get('group_by', 'day')  # group the trend by "day" or by "month"
    if group_by not in ('day', 'month'):
        group_by = 'day'  # fall back to day if someone passes a bad value in the url

    appointments = Appointment.objects.select_related('payment').all()  # every appointment, with its payment attached
    if start_date:
        appointments = appointments.filter(date__gte=start_date)  # drop appointments before the "from" date
    if end_date:
        appointments = appointments.filter(date__lte=end_date)  # drop appointments after the "to" date

    # one counter dict per time bucket (a day or a month), built by walking the appointments once
    buckets = {}
    for appointment in appointments:
        if group_by == 'month':
            key = appointment.date.strftime('%Y-%m')  # bucket by year and month, e.g. "2026-08"
        else:
            key = appointment.date.strftime('%Y-%m-%d')  # bucket by the exact day
        row = buckets.setdefault(key, {'label': key, 'appointment_count': 0, 'revenue': 0})  # start this bucket at zero the first time we see it
        row['appointment_count'] += 1  # one more appointment in this bucket
        payment = getattr(appointment, 'payment', None)  # this appointment's payment row, or None
        if payment and payment.status == 'paid':
            row['revenue'] += payment.amount  # add to this bucket's paid revenue

    trend_rows = [buckets[key] for key in sorted(buckets)]  # oldest bucket first, since the keys sort chronologically as plain text

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'group_by': group_by,
        'trend_rows': trend_rows,
        'total_appointments': sum(row['appointment_count'] for row in trend_rows),
        'total_revenue': sum(row['revenue'] for row in trend_rows),
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/appointment_revenue_trend_pdf.html', context, 'appointment_revenue_trend.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/appointment_revenue_trend.html', context)


# shows every consultation payment and pharmacy order that has not been paid yet
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def outstanding_payments_report(request):
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    context = {'start_date': start_date, 'end_date': end_date}

    # every consultation payment that has not been paid yet
    pending_payments = Payment.objects.filter(status='pending').select_related('appointment__patient', 'appointment__doctor').order_by('appointment__date')
    if start_date:
        pending_payments = pending_payments.filter(appointment__date__gte=start_date)  # drop rows before the "from" date
    if end_date:
        pending_payments = pending_payments.filter(appointment__date__lte=end_date)  # drop rows after the "to" date

    # every pharmacy order that has not been paid yet
    pending_orders = PharmacyOrder.objects.filter(payment_status='pending').select_related('appointment__patient').order_by('appointment__date')
    if start_date:
        pending_orders = pending_orders.filter(appointment__date__gte=start_date)  # drop rows before the "from" date
    if end_date:
        pending_orders = pending_orders.filter(appointment__date__lte=end_date)  # drop rows after the "to" date

    consultation_total = 0  # add up every unpaid consultation amount
    for payment in pending_payments:
        consultation_total += payment.amount

    pharmacy_total = 0  # add up every unpaid pharmacy order amount
    for order in pending_orders:
        pharmacy_total += order.total_amount

    context['pending_payments'] = pending_payments
    context['pending_orders'] = pending_orders
    context['consultation_total'] = consultation_total
    context['pharmacy_total'] = pharmacy_total
    context['grand_total'] = consultation_total + pharmacy_total

    pdf_response = export_pdf(request, 'dashboard/report_management/outstanding_payments_pdf.html', context, 'outstanding_payments.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/outstanding_payments.html', context)


# shows every medicine in the catalog with how many units are currently in stock
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def stock_inventory_report(request):
    query = request.GET.get('q', '')  # the search text typed in the search box
    context = {'query': query}

    medicines = Medicine.objects.all().order_by('name')  # every medicine, alphabetical
    if query:
        medicines = medicines.filter(name__icontains=query)  # only medicines whose name matches the search text

    if request.GET.get('download') == 'pdf':
        # the pdf gets the full list, not just one page
        context['medicines'] = medicines
        pdf_response = export_pdf(request, 'dashboard/report_management/stock_inventory_pdf.html', context, 'stock_inventory.pdf')  # build the pdf, or None if not asked for
        if pdf_response:
            return pdf_response  # send the pdf back to the browser

    # the on-screen page shows 25 medicines at a time, so the list stays fast even with a big catalog
    paginator = Paginator(medicines, 25)  # split the queryset into pages of 25 rows each
    page_number = request.GET.get('page')  # which page the user asked for, from the url
    context['page_obj'] = paginator.get_page(page_number)  # the one page of medicines to show right now

    return render(request, 'dashboard/report_management/stock_inventory.html', context)


# shows which doctors have appointments booked, slot by slot, on a chosen day
@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def doctor_schedule_report(request):
    schedule_date = request.GET.get('schedule_date') or str(date.today())  # default to today if nothing was picked
    context = {'schedule_date': schedule_date}

    # the fixed one hour slots a doctor can be booked into, skipping the blank "Select Time Slot" choice
    time_slots = [(value, label) for value, label in Appointment.TIME_SLOT_CHOICES if value]

    if request.user.profile.role == 'doctor':
        # a doctor always sees only their own day, ignoring ?doctor_id= in the url
        doctors = [request.user]
    else:
        doctor_id = request.GET.get('doctor_id', '')
        if doctor_id:
            doctors = [get_object_or_404(User, pk=doctor_id, profile__role='doctor')]  # just the one doctor picked
        else:
            # no doctor picked, so show every doctor who has an appointment on this date
            doctors = User.objects.filter(profile__role='doctor', doctor_appointments__date=schedule_date).distinct().order_by('first_name', 'last_name')
        context['doctors'] = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')  # feeds the doctor drop-down
        context['doctor_id'] = doctor_id

    schedules = []  # one entry per doctor, each with their full slot grid for the day
    for doctor in doctors:
        # this doctor's appointments on this date, ignoring cancelled ones since a cancelled slot is free again
        appointments = Appointment.objects.filter(doctor=doctor, date=schedule_date).exclude(status='cancelled').select_related('patient')
        appointment_by_slot = {appointment.time_slot: appointment for appointment in appointments}  # look up an appointment by its slot code

        slots = [{'label': label, 'appointment': appointment_by_slot.get(value)} for value, label in time_slots]  # every slot, booked or free
        schedules.append({'doctor': doctor, 'slots': slots})

    context['schedules'] = schedules

    pdf_response = export_pdf(request, 'dashboard/report_management/doctor_schedule_pdf.html', context, 'doctor_schedule.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/doctor_schedule.html', context)


# shows every patient grouped by age group and by gender
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def patient_demographics_report(request):
    patients = PatientProfile.objects.select_related('user__profile').all()  # every patient, with their profile attached

    # counters for each age group, kept in display order
    age_group_counts = {'0-17': 0, '18-35': 0, '36-50': 0, '51-65': 0, '65+': 0, 'Unknown': 0}
    # turns the short gender code into a readable label
    gender_labels = {'male': 'Male', 'female': 'Female', 'other': 'Other'}
    gender_counts = {'Male': 0, 'Female': 0, 'Other': 0, 'Not specified': 0}

    for patient in patients:
        age = patient.age  # uses the model's own age property, or None if the date of birth is unknown
        if age is None:
            age_group_counts['Unknown'] += 1
        elif age <= 17:
            age_group_counts['0-17'] += 1
        elif age <= 35:
            age_group_counts['18-35'] += 1
        elif age <= 50:
            age_group_counts['36-50'] += 1
        elif age <= 65:
            age_group_counts['51-65'] += 1
        else:
            age_group_counts['65+'] += 1

        gender_code = patient.user.profile.gender  # 'male' / 'female' / 'other' / blank
        gender_label = gender_labels.get(gender_code, 'Not specified')  # blank or unknown code falls back to "Not specified"
        gender_counts[gender_label] += 1

    context = {
        'age_group_stats': [{'label': label, 'count': count} for label, count in age_group_counts.items()],
        'gender_stats': [{'label': label, 'count': count} for label, count in gender_counts.items()],
        'total_patients': patients.count(),
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/patient_demographics_pdf.html', context, 'patient_demographics.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/patient_demographics.html', context)


# shows every consultation payment that was paid, then refunded to the patient
@login_required
@required_role(['admin'], 'You do not have permission to view reports.')
def refund_report(request):
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    context = {'start_date': start_date, 'end_date': end_date}

    # every consultation payment that was refunded; pharmacy orders have no "refunded" status in this system
    refunds = Payment.objects.filter(status='refunded').select_related('appointment__patient', 'appointment__doctor').order_by('-appointment__date')
    if start_date:
        refunds = refunds.filter(appointment__date__gte=start_date)  # drop rows before the "from" date
    if end_date:
        refunds = refunds.filter(appointment__date__lte=end_date)  # drop rows after the "to" date

    total_refunded = 0  # add up every refunded amount
    for payment in refunds:
        total_refunded += payment.amount

    context['refunds'] = refunds
    context['total_refunded'] = total_refunded

    pdf_response = export_pdf(request, 'dashboard/report_management/refund_report_pdf.html', context, 'refund_report.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/refund_report.html', context)


# shows medicine stock batches bought from each supplier, and their total cost
@login_required
@required_role(['admin', 'pharmacist'], 'You do not have permission to view reports.')
def purchase_report(request):
    start_date = request.GET.get('start_date', '')  # read the "from" date typed in the filter form
    end_date = request.GET.get('end_date', '')  # read the "to" date typed in the filter form
    supplier_id = request.GET.get('supplier_id', '')  # which supplier was picked in the filter form

    # only batches with a known purchase price count as a real purchase
    batches = MedicineStock.objects.select_related('medicine', 'supplier').filter(purchase_price__isnull=False)
    if start_date:
        batches = batches.filter(received_date__gte=start_date)  # drop batches received before the "from" date
    if end_date:
        batches = batches.filter(received_date__lte=end_date)  # drop batches received after the "to" date
    if supplier_id:
        batches = batches.filter(supplier_id=supplier_id)  # only this one supplier, if chosen

    # group the batches by supplier, adding up batch count, quantity, and total cost per supplier
    supplier_summary = batches.values('supplier__id', 'supplier__name').annotate(
        batch_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('purchase_price')),
    ).order_by('-total_cost')

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'supplier_id': supplier_id,
        'suppliers': Supplier.objects.all().order_by('name'),  # feeds the supplier drop-down
        'supplier_summary': supplier_summary,
        'batches': batches.order_by('-received_date'),
        'grand_total_value': sum(row['total_cost'] or 0 for row in supplier_summary),  # add up every supplier's total cost
    }

    pdf_response = export_pdf(request, 'dashboard/report_management/purchase_report_pdf.html', context, 'purchase_report.pdf')  # build the pdf, or None if not asked for
    if pdf_response:
        return pdf_response  # send the pdf back to the browser

    return render(request, 'dashboard/report_management/purchase_report.html', context)
