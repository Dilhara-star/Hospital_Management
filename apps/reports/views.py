from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string  # turns a template into an HTML string, used for PDFs
from django.http import HttpResponse
from apps.appointment.models import Appointment  # the appointment + payment rows reports are built from
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role


@login_required
@required_role(['admin', 'doctor'], 'You do not have permission to view reports.')
def reports_index(request):
    return render(request, 'dashboard/report_management/index.html')


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
        # PDF download උනත් doctor කෙනෙක් තෝරලා නැත්නම් error එකක් දාලා report page එකට ආපහු යනවා
        if doctor is None:
            messages.error(request, 'Please choose a doctor first.')
            return redirect('doctor_revenue_report')

        from xhtml2pdf import pisa  # HTML එකක් PDF file එකක් බවට හරවන library එක, මේ තැනට විතරක් ඕන නිසා මෙතනදීම import කරනවා
        html = render_to_string('dashboard/report_management/doctor_revenue_pdf.html', context)  # data එක සමග template එක render කරලා HTML string එකක් හදනවා
        response = HttpResponse(content_type='application/pdf')  # මේක PDF file එකක් කියලා browser එකට කියනවා
        response['Content-Disposition'] = f'attachment; filename="doctor_revenue_{doctor.pk}.pdf"'  # download prompt එකක් පෙන්නන්න force කරනවා
        pisa.CreatePDF(html, dest=response)  # HTML එක PDF එකක් බවට convert කරලා response එකට ලියනවා
        return response  # PDF file එක browser එකට යවනවා

    return render(request, 'dashboard/report_management/doctor_revenue.html', context)


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
        # PDF download උනත් doctor කෙනෙක් තෝරලා නැත්නම් error එකක් දාලා report page එකට ආපහු යනවා
        if doctor is None:
            messages.error(request, 'Please choose a doctor first.')
            return redirect('appointment_summary_report')

        from xhtml2pdf import pisa  # HTML එකක් PDF file එකක් බවට හරවන library එක, මේ තැනට විතරක් ඕන නිසා මෙතනදීම import කරනවා
        html = render_to_string('dashboard/report_management/appointment_summary_pdf.html', context)  # data එක සමග template එක render කරලා HTML string එකක් හදනවා
        response = HttpResponse(content_type='application/pdf')  # මේක PDF file එකක් කියලා browser එකට කියනවා
        response['Content-Disposition'] = f'attachment; filename="appointment_summary_{doctor.pk}.pdf"'  # download prompt එකක් පෙන්නන්න force කරනවා
        pisa.CreatePDF(html, dest=response)  # HTML එක PDF එකක් බවට convert කරලා response එකට ලියනවා
        return response  # PDF file එක browser එකට යවනවා

    return render(request, 'dashboard/report_management/appointment_summary.html', context)
