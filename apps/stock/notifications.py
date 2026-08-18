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


# checks one medicine's stock against its own reorder level, and emails admin + supplier if it is low
def notify_low_stock(medicine):
    # call this after anything that can change a medicine's total stock or reorder level
    # (adding/editing/deleting a stock batch, editing the medicine, dispensing medicine).
    # uses the same rule as the "Low Stock" badge on the medicine list page.
    if not medicine.is_low_stock:
        return  # stock is fine, nothing to send

    remaining_stock = medicine.total_quantity  # fresh total, read once for both emails below
    send_low_stock_admin_email(medicine, remaining_stock)
    send_low_stock_supplier_email(medicine, remaining_stock)


# emails the admin once a medicine's stock drops to or below its reorder level
def send_low_stock_admin_email(medicine, remaining_stock):
    # any failure here (no internet, wrong api key, brevo is down) is only printed to the
    # console - it must never crash the page that triggered this check.
    to_email = settings.ADMIN_NOTIFY_EMAIL  # where the email goes
    if not to_email:
        return  # no admin email configured, nothing we can send

    subject = f'Low Stock Alert - {medicine.name} ({remaining_stock} units left)'  # email subject line

    # build the email body from the template file, filling in the medicine details
    html_content = render_to_string('emails/stock/remaining_stock_mail_admin.html', {
        'medicine': medicine,
        'remaining_stock': remaining_stock,
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
        # brevo could not be reached - just log it
        print(f'Could not send low stock admin email: {error}')


# emails the supplier once a medicine's stock drops to or below its reorder level
def send_low_stock_supplier_email(medicine, remaining_stock):
    # any failure here is only printed to the console - it must never crash the page
    # that triggered this check.

    # find the supplier who sent the most recent stock batch for this medicine
    last_batch = medicine.stock_batches.exclude(supplier__isnull=True).order_by('-received_date').first()
    if not last_batch or not last_batch.supplier.email:
        return  # no supplier email on file for this medicine, nothing we can send

    supplier = last_batch.supplier  # the supplier to notify
    to_email = supplier.email  # where the email goes

    subject = f'Restock Needed - {medicine.name} ({remaining_stock} units left)'  # email subject line

    # build the email body from the template file, filling in the medicine details
    html_content = render_to_string('emails/stock/remaining_stock_mail_supplier.html', {
        'medicine': medicine,
        'remaining_stock': remaining_stock,
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
        # brevo could not be reached - just log it
        print(f'Could not send low stock supplier email: {error}')
