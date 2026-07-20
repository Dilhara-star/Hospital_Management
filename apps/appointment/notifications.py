import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from apps.user_management.models import StaffProfile  # holds the room number for a doctor


def _room_for(doctor):
    # same lookup used on the appointment pages: the room number staff assigned to this doctor
    if not doctor or not hasattr(doctor, 'profile'):
        return 'Not assigned yet'  # no doctor picked yet, so there is no room
    try:
        room = doctor.profile.staff_profile.room_number  # look up the room saved for this doctor
        return room or 'Not assigned yet'  # room field can exist but be empty
    except StaffProfile.DoesNotExist:
        return 'Not assigned yet'  # this doctor has no staff profile row yet


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

    subject = f'Appointment Confirmed - {appointment_number}'  # email subject line

    # the email body, with the appointment number, time and room number the user asked for
    html_content = f"""
    <p>Dear {appointment.patient_name},</p>
    <p>Your appointment has been <strong>confirmed</strong>. Here are the details:</p>
    <ul>
        <li><strong>Appointment Number:</strong> {appointment_number}</li>
        <li><strong>Date:</strong> {appointment.date.strftime('%d %b %Y')}</li>
        <li><strong>Time:</strong> {appointment.get_time_slot_display()}</li>
        <li><strong>Doctor:</strong> {doctor_name}</li>
        <li><strong>Room Number:</strong> {room_number}</li>
        <li><strong>Department:</strong> {appointment.get_department_display()}</li>
    </ul>
    <p>Please arrive 10 minutes before your appointment time.</p>
    <p>Thank you,<br>{settings.BREVO_SENDER_NAME}</p>
    """

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
