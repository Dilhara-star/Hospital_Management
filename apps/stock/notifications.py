import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an html string


# emails the admin a digest of every stock batch that has expired or is expiring soon
def send_expiry_alert_admin_email(expired_batches, expiring_batches):
    # emails the hospital admin one digest listing every stock batch that has already
    # expired or is expiring soon. meant to be called from a scheduled management
    # command, not from a view - but the same "print, never crash" rule still applies.
    to_email = settings.ADMIN_NOTIFY_EMAIL  # where the email goes
    if not to_email:
        return  # no admin email configured, nothing we can send

    subject = 'Medicine Stock Expiry Alert'  # email subject line

    # build the email body from the template file, filling in both batch lists
    html_content = render_to_string('emails/stock/expiry_alert_admin.html', {
        'expired_batches': expired_batches,
        'expiring_batches': expiring_batches,
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
        # 10 second timeout, so a slow or dead brevo api can never hang the command
        requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
    except requests.RequestException as error:
        # brevo could not be reached - just log it
        print(f'Could not send expiry alert admin email: {error}')
