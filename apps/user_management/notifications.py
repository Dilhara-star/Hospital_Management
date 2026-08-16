import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an HTML string


# emails a "reset your password" link to someone who used the forgot password page
def send_password_reset_email(user, reset_link):
    # emails a "reset your password" link to someone who used the forgot password page.
    # any failure here is only printed to the console - it must never crash the forgot password page.
    to_email = user.email  # where the email goes
    if not to_email:
        return  # this account has no email saved, nothing we can send

    subject = 'Reset Your Password'  # email subject line

    # build the email body from the template file, filling in the user and the reset link
    html_content = render_to_string('emails/auth/password_reset.html', {
        'user': user,
        'reset_link': reset_link,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': user.get_full_name()}],
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
        # brevo could not be reached - just log it
        print(f'Could not send password reset email: {error}')


# emails a brand new staff member their login username
def send_staff_welcome_email(user, role):
    # emails a brand new staff member their login username after an admin creates their account.
    # any failure here (no internet, wrong api key, brevo is down) is only printed to the
    # console - it must never crash the "add staff" page for the admin waiting on it.
    to_email = user.email  # where the email goes
    if not to_email:
        return  # this staff account has no email saved, nothing we can send

    subject = 'Welcome to Medi Plus'  # email subject line

    # build the email body from the template file, filling in the user, role and sender name
    html_content = render_to_string('emails/auth/staff_welcome.html', {
        'user': user,
        'role': role,
        'sender_name': settings.BREVO_SENDER_NAME,
    })
    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': user.get_full_name()}],
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
        # brevo could not be reached - just log it, the staff account is still created either way
        print(f'Could not send staff welcome email: {error}')


# emails a patient when their insurance policy is about to expire
def send_insurance_expiry_email(patient_profile):
    # emails a patient when their insurance policy is about to expire. meant to be
    # called from a scheduled management command, not from a view - but the same
    # "print, never crash" rule still applies.
    patient_user = patient_profile.user  # the login account linked to this patient record
    to_email = patient_user.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    subject = 'Your Insurance is Expiring Soon'  # email subject line

    # build the email body from the template file, filling in the patient and insurance details
    html_content = render_to_string('emails/patient/insurance_expiry_reminder.html', {
        'patient': patient_profile,
        'user': patient_user,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': patient_user.get_full_name()}],
        'subject': subject,
        'htmlContent': html_content,
    }
    headers = {
        'accept': 'application/json',
        'api-key': settings.BREVO_API_KEY,  # brevo checks this key to know who is sending
        'content-type': 'application/json',
    }

    try:
        # 10 second timeout, so a slow or dead brevo api can never hang the command
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it
        print(f'Could not send insurance expiry email: {error}')


# emails a patient once their status is changed to "discharged" by staff
def send_patient_discharge_email(patient_user):
    # emails a patient once their status is changed to "discharged" by staff.
    # any failure here is only printed to the console - it must never crash the "edit patient" page.
    to_email = patient_user.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    subject = 'You Have Been Discharged'  # email subject line

    # build the email body from the template file, filling in the patient details
    html_content = render_to_string('emails/patient/discharge_notice.html', {
        'user': patient_user,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': patient_user.get_full_name()}],
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
        # brevo could not be reached - just log it, the status is still saved either way
        print(f'Could not send patient discharge email: {error}')


# emails a brand new patient their login username after they sign up or are registered by staff
def send_patient_welcome_email(user):
    # any failure here (no internet, wrong api key, brevo is down) is only printed to the
    # console - it must never crash the sign up / "add patient" page waiting on it.
    to_email = user.email  # where the email goes
    if not to_email:
        return  # this patient account has no email saved, nothing we can send

    subject = 'Welcome to Medi Plus'  # email subject line

    # build the email body from the template file, filling in the user and sender name
    html_content = render_to_string('emails/auth/patient_welcome.html', {
        'user': user,
        'sender_name': settings.BREVO_SENDER_NAME,
    })
    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': user.get_full_name()}],
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
        # brevo could not be reached - just log it, the patient account is still created either way
        print(f'Could not send patient welcome email: {error}')

