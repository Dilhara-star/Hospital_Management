import requests  # used to call the Brevo email api
from django.conf import settings  # holds the brevo api key and sender details
from django.template.loader import render_to_string  # turns the email template into an HTML string


# emails the patient once their medicine has been handed out and is awaiting payment
def send_medicine_dispensed_email(order):
    # emails the patient once the pharmacist has handed out their medicine, but before
    # payment is taken - lets them know to pay at the counter. any failure here is only
    # printed to the console - it must never crash the pharmacist's dispense action.
    appointment = order.appointment  # the appointment this pharmacy order belongs to
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    # medicines on this order, with medicine details attached
    prescribed_items = appointment.prescription_items.select_related('medicine').all()

    # one row per medicine, with its unit price and subtotal worked out fresh from the catalog price
    billed_items = []
    for item in prescribed_items:
        unit_price = item.medicine.price  # current catalog price for this medicine
        billed_items.append({
            'name': item.medicine.name,
            'quantity': item.quantity,
            'unit_price': unit_price,
            'subtotal': unit_price * item.quantity,
        })
    medicine_total = sum(row['subtotal'] for row in billed_items)  # total of every row above

    subject = f'Your Medicine is Ready - Please Pay - APT-{appointment.pk:06d}'  # email subject line

    # build the email body from the template file, filling in the order details
    html_content = render_to_string('emails/pharmacy/medicine_dispensed.html', {
        'order': order,
        'billed_items': billed_items,
        'medicine_total': medicine_total,
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
        # brevo could not be reached - just log it, the order is still saved either way
        print(f'Could not send medicine dispensed email: {error}')


# emails the patient once their prescribed medicine has been paid for
def send_medicine_payment_confirmation_email(order):
    # emails the patient once their prescribed medicine has been paid for, whether they
    # paid online themselves or paid cash to the pharmacist. any failure here is only
    # printed to the console - it must never crash the payment action.
    appointment = order.appointment  # the appointment this pharmacy order belongs to
    to_email = appointment.patient.email  # where the email goes
    if not to_email:
        return  # this patient has no email saved, nothing we can send

    # medicines on this order, with medicine details attached
    prescribed_items = appointment.prescription_items.select_related('medicine').all()

    # one row per medicine, with its unit price and subtotal worked out fresh from the catalog price
    billed_items = []
    for item in prescribed_items:
        unit_price = item.medicine.price  # current catalog price for this medicine
        billed_items.append({
            'name': item.medicine.name,
            'quantity': item.quantity,
            'unit_price': unit_price,
            'subtotal': unit_price * item.quantity,
        })
    medicine_total = sum(row['subtotal'] for row in billed_items)  # total of every row above

    subject = f'Medicine Payment Received - {order.transaction_ref}'  # email subject line

    # build the email body from the template file, filling in the order and payment details
    html_content = render_to_string('emails/pharmacy/medicine_payment_confirmation.html', {
        'order': order,
        'billed_items': billed_items,
        'medicine_total': medicine_total,
        'payment_method': order.get_payment_method_display(),
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
        # brevo could not be reached - just log it, the payment is still saved either way
        print(f'Could not send medicine payment confirmation email: {error}')
