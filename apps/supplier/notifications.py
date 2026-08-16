import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an html string


# emails a supplier once they are added to the hospital's supplier list
def send_supplier_welcome_email(supplier):
    # emails a supplier once they are added to the hospital's supplier list.
    # any failure here is only printed to the console - it must never crash the "add supplier" page.
    to_email = supplier.email  # where the email goes
    if not to_email:
        return  # this supplier has no email saved, nothing we can send

    subject = 'You Have Been Added as a Supplier'  # email subject line

    # build the email body from the template file, filling in the supplier details
    html_content = render_to_string('emails/supplier/supplier_welcome.html', {
        'supplier': supplier,
        'sender_name': settings.BREVO_SENDER_NAME,
    })

    # the data brevo's transactional email api expects
    payload = {
        'sender': {'name': settings.BREVO_SENDER_NAME, 'email': settings.BREVO_SENDER_EMAIL},
        'to': [{'email': to_email, 'name': supplier.name}],
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
        # brevo could not be reached - just log it, the supplier is still saved either way
        print(f'Could not send supplier welcome email: {error}')
