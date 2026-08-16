import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an html string


# emails the hospital admin whenever a visitor submits the "Contact Us" form
def send_contact_inquiry_admin_email(inquiry):
    # emails the hospital admin whenever a visitor submits the "Contact Us" form.
    # any failure here (no internet, wrong api key, brevo is down) is only printed to the
    # console - it must never crash the contact page for the visitor waiting on it.
    to_email = settings.ADMIN_NOTIFY_EMAIL  # where the email goes
    if not to_email:
        return  # no admin email configured, nothing we can send

    subject = f'New Contact Message - {inquiry.subject or inquiry.name}'  # email subject line

    # build the email body from the template file, filling in the inquiry details
    html_content = render_to_string('emails/contact/new_inquiry_admin.html', {
        'inquiry': inquiry,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': 'Admin'}],
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
        # brevo could not be reached - just log it, the inquiry is still saved either way
        print(f'Could not send contact inquiry admin email: {error}')


# emails the sender once their "Contact Us" message is marked solved
def send_contact_resolved_email(inquiry):
    # emails the person who sent a "Contact Us" message once an admin marks it solved.
    # any failure here is only printed to the console - it must never crash the dashboard action.
    to_email = inquiry.email  # where the email goes
    if not to_email:
        return  # this inquiry has no email saved, nothing we can send

    subject = 'Your Inquiry Has Been Resolved'  # email subject line

    # build the email body from the template file, filling in the inquiry details
    html_content = render_to_string('emails/contact/inquiry_resolved.html', {
        'inquiry': inquiry,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': inquiry.name}],
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
        print(f'Could not send contact resolved email: {error}')
