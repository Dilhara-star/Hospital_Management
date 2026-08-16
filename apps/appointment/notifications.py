import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an HTML string
from apps.user_management.models import StaffProfile  # holds the room number for a doctor


# looks up a doctor's assigned room number, for use inside the email templates below
def _room_for(doctor):
    # same lookup used on the appointment pages: the room number staff assigned to this doctor
    if not doctor or not hasattr(doctor, 'profile'):
        return 'Not assigned yet'  # no doctor picked yet, so there is no room
    try:
        room = doctor.staff_profile.room_number  # look up the room saved for this doctor
        return room or 'Not assigned yet'  # room field can exist but be empty
    except StaffProfile.DoesNotExist:
        return 'Not assigned yet'  # this doctor has no staff profile row yet

# emails the patient once their appointment is confirmed
def send_appointment_confirmation_email(appointment):
    # emails the patient once their appointment is confirmed (paid online, or cash
    # confirmed at reception). any failure here (no internet, wrong api key, brevo
    # is down) is only printed to the console - it must never crash the booking
    # or payment page for the patient/staff member waiting on it.
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'  # doctor's name
    room_number = _room_for(appointment.doctor)  # room number for that doctor

    payment = getattr(appointment, 'payment', None)  # the payment row, so the email can show a bill breakdown
    department_fee = (payment.amount - payment.doctor_fee_amount) if payment else 0  # hospital's own base charge
    doctor_fee = payment.doctor_fee_amount if payment else 0  # just the doctor's own cut

    subject = f'Appointment Confirmed - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the appointment and bill details
    html_content = render_to_string('emails/appointment/confirmation.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'room_number': room_number,
        'payment': payment,
        'department_fee': department_fee,
        'doctor_fee': doctor_fee,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the appointment is still confirmed either way
        print(f'Could not send appointment confirmation email: {error}')

# emails the admin once a new appointment is confirmed
def send_appointment_confirmation_email_admin(appointment):
    # emails the patient once their appointment is confirmed (paid online, or cash
    # confirmed at reception). any failure here (no internet, wrong api key, brevo
    # is down) is only printed to the console - it must never crash the booking
    # or payment page for the patient/staff member waiting on it.
    to_email = settings.ADMIN_NOTIFY_EMAIL  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'  # doctor's name
    room_number = _room_for(appointment.doctor)  # room number for that doctor

    subject = f'Appointment Confirmed - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the appointment details
    html_content = render_to_string('emails/appointment/confirmation_to_admin.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'room_number': room_number,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the appointment is still confirmed either way
        print(f'Could not send appointment confirmation email: {error}')

# emails the patient a newly booked appointment that is still waiting on payment
def send_email_appointment_without_payment(appointment):
    to_email = appointment.patient.email
    if not to_email:
        return

    appointment_number = f'APT-{appointment.pk:06d}'
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'
    room_number = _room_for(appointment.doctor)

    subject = f'New Appointment Booked | Pending Payment  - {appointment_number}'

    html_content = render_to_string('emails/appointment/without_payment_to_customer.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'room_number': room_number,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,
        'content-type': 'application/json',
    }

    try:
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        print(f'Could not send appointment notification email: {error}')


# emails the patient once they reschedule their own appointment
def send_appointment_update_email(appointment):
    # emails the patient when they reschedule their own appointment's date or time.
    # any failure here is only printed to the console - it must never crash the reschedule page.
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'  # doctor's name
    room_number = _room_for(appointment.doctor)  # room number for that doctor

    subject = f'Appointment Rescheduled - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the new appointment details
    html_content = render_to_string('emails/appointment/update_confirmation.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'room_number': room_number,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the reschedule is still saved either way
        print(f'Could not send appointment update email: {error}')


# emails the patient once their appointment has been cancelled
def send_appointment_cancellation_email(appointment):
    # emails the patient once their appointment has been cancelled (cash payment, or no
    # payment made yet - the online-refund case has its own email below). any failure
    # here is only printed to the console - it must never crash the cancel action.
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'  # doctor's name

    subject = f'Appointment Cancelled - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the cancelled appointment details
    html_content = render_to_string('emails/appointment/cancellation.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the cancellation is still saved either way
        print(f'Could not send appointment cancellation email: {error}')


# emails the patient once their online payment has been refunded
def send_appointment_refund_email(appointment):
    # emails the patient once their online-paid appointment has been cancelled and the
    # demo refund has been processed. any failure here is only printed to the console -
    # it must never crash the refund action.
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    payment = appointment.payment  # the payment row, now marked as refunded
    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    doctor_name = appointment.doctor.get_full_name() if appointment.doctor else 'Not assigned yet'  # doctor's name

    subject = f'Appointment Cancelled & Refund Processed - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the cancelled appointment and refund details
    html_content = render_to_string('emails/appointment/refund_confirmation.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'doctor_name': doctor_name,
        'payment': payment,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.patient_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the refund is still saved either way
        print(f'Could not send appointment refund email: {error}')


# emails a doctor once they are assigned to an appointment
def send_doctor_assignment_email(appointment):
    # emails a doctor once they are assigned (or reassigned) to an appointment, so they
    # know a new patient is on their schedule. any failure here is only printed to the
    # console - it must never crash the booking or edit page for the staff member waiting on it.
    to_email = appointment.doctor.email  # where the email goes
    if not to_email:
        return  # this doctor has no email saved, nothing we can send

    appointment_number = f'APT-{appointment.pk:06d}'  # same numbering style as the receipt refs
    room_number = _room_for(appointment.doctor)  # room number for that doctor

    subject = f'New Appointment Assigned - {appointment_number}'  # email subject line

    # build the email body from the template file, filling in the appointment details
    html_content = render_to_string('emails/appointment/doctor_assigned.html', {
        'appointment': appointment,
        'appointment_number': appointment_number,
        'room_number': room_number,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': appointment.doctor.get_full_name()}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never freeze the page
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it, the appointment is still saved either way
        print(f'Could not send doctor assignment email: {error}')

# note: medicine dispensed/payment emails live in apps/pharmacy/notifications.py, and
# low stock alert emails live in apps/inventory/notifications.py - both are pharmacy/stock
# concerns, not appointment-booking concerns