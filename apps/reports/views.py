from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.core.paginator import Paginator  # splits a long list of appointments into pages
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string  # turns a template into an HTML string, used for PDFs
from django.http import HttpResponse
from apps.appointment.models import Appointment, DepartmentFee  # the rows reports are built from
from apps.pharmacy.models import PharmacyOrder  # the medicine orders pharmacy revenue reports are built from
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role


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

        from xhtml2pdf import pisa  # html to pdf library, only needed here so it is imported at this point
        html = render_to_string('dashboard/report_management/doctor_revenue_pdf.html', context)  # turn the template into an html string, filled in with this report's data
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a pdf file
        response['Content-Disposition'] = f'attachment; filename="doctor_revenue_{doctor.pk}.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the html into a pdf and write it into the response
        return response  # send the pdf back to the browser

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

        from xhtml2pdf import pisa  # html to pdf library, only needed here so it is imported at this point
        html = render_to_string('dashboard/report_management/appointment_summary_pdf.html', context)  # turn the template into an html string, filled in with this report's data
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a pdf file
        response['Content-Disposition'] = f'attachment; filename="appointment_summary_{doctor.pk}.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the html into a pdf and write it into the response
        return response  # send the pdf back to the browser

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

    if request.GET.get('download') == 'pdf':
        from xhtml2pdf import pisa  # only needed here, so it is imported right at this point
        html = render_to_string('dashboard/report_management/hospital_revenue_pdf.html', context)  # turn the template into an HTML string
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a PDF file
        response['Content-Disposition'] = 'attachment; filename="hospital_revenue.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the HTML string into a real PDF, written into the response
        return response  # send the PDF back to the browser

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

    if request.GET.get('download') == 'pdf':
        from xhtml2pdf import pisa  # only needed here, so it is imported right at this point
        html = render_to_string('dashboard/report_management/department_performance_pdf.html', context)  # build the PDF's HTML
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a PDF file
        response['Content-Disposition'] = 'attachment; filename="department_performance.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the HTML string into a real PDF
        return response  # send the PDF back to the browser

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

    if request.GET.get('download') == 'pdf':
        from xhtml2pdf import pisa  # only needed here, so it is imported right at this point
        html = render_to_string('dashboard/report_management/doctors_leaderboard_pdf.html', context)  # build the PDF's HTML
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a PDF file
        response['Content-Disposition'] = 'attachment; filename="doctors_leaderboard.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the HTML string into a real PDF
        return response  # send the PDF back to the browser

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
        from xhtml2pdf import pisa  # only needed here, so it is imported right at this point
        html = render_to_string('dashboard/report_management/appointment_status_pdf.html', context)  # build the PDF's HTML
        response = HttpResponse(content_type='application/pdf')  # tell the browser this reply is a PDF file
        response['Content-Disposition'] = 'attachment; filename="appointment_status.pdf"'  # force a download prompt
        pisa.CreatePDF(html, dest=response)  # turn the HTML string into a real PDF
        return response  # send the PDF back to the browser

    # the on-screen page shows 25 appointments at a time, so the list stays fast even with many rows
    paginator = Paginator(appointments, 25)  # split the queryset into pages of 25 rows each
    page_number = request.GET.get('page')  # which page the user asked for, from the URL
    context['page_obj'] = paginator.get_page(page_number)  # the one page of appointments to show right now

    return render(request, 'dashboard/report_management/appointment_status.html', context)
