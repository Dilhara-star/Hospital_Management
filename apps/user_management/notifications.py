import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an HTML string


def send_staff_welcome_email(user, role):
    # emails a brand new staff member their login username after an admin creates their account.
    # any failure here (no internet, wrong api key, brevo is down) is only printed to the
    # console - it must never crash the "add staff" page for the admin waiting on it.
    to_email = user.email  # where the email goes
    if not to_email:
        return  # this staff account has no email saved, nothing we can send

    subject = 'Welcome to City Hospital'  # email subject line

    # build the email body from the template file, filling in the user, role and sender name
    html_content = render_to_string('emails/staff_welcome.html', {
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
