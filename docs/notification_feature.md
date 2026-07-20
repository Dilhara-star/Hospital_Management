# Appointment Confirmation Email

This is the reference doc for the confirmation email feature, alongside the two
PDF guides in the project root. Follow this shape when touching this feature again.

## What this feature does

When an appointment becomes **confirmed** — either because the patient paid
online during booking, or because reception confirmed a cash payment at the
hospital — the patient gets an email with their appointment number, date, time,
doctor, and room number. Sent through [Brevo](https://www.brevo.com)'s
transactional email API.

## Where it's sent from (`apps/appointment/views.py`)

- `_record_payment()` — shared by patient online booking and staff "Add
  Appointment". When `payment_method == 'online'` (or staff mark cash as
  already received), the appointment is confirmed immediately, and the email
  is sent right after the `Payment` row is created.
- `confirm_cash_payment()` — reception/admin only. Confirms a pending cash
  payment, sets `appointment.status = 'confirmed'`, then sends the email.

Both call the one function below — there is no signal, no queue, just a plain
function call right after the appointment is saved as confirmed.

## The email itself (`apps/appointment/notifications.py`)

- `send_appointment_confirmation_email(appointment)` — builds the subject and
  HTML body (appointment number as `APT-000123`, date, time slot, doctor name,
  room number, department) and posts it to
  `https://api.brevo.com/v3/smtp/email`.
- Sends to `appointment.patient.email` (the logged-in `User`'s email). If the
  patient has no email saved, the function just returns — nothing to send.
- Room number comes from the same lookup used elsewhere
  (`doctor.profile.staff_profile.room_number`), duplicated locally as
  `_room_for()` so this file has no import back into `views.py`.
- Wrapped in `try/except requests.RequestException` — if Brevo is unreachable
  or the API key is wrong, the error is only printed to the console. Sending
  the email must never break the booking or payment page.

## Setup (`.env`)

Brevo settings are read from a `.env` file in the project root (gitignored),
loaded in `Hospital_Management/settings.py` with `python-dotenv`:

```
BREVO_API_KEY=your-brevo-api-key-here
BREVO_SENDER_EMAIL=your-verified-sender@example.com
BREVO_SENDER_NAME=City Hospital
```

Copy `.env.example` to `.env` and fill in your real values. See the Brevo
setup steps below for where to get the API key and how to verify a sender
email — no domain is required, a single verified email address is enough.

## Getting a Brevo API key (no domain needed)

1. Sign up for a free account at [brevo.com](https://www.brevo.com) (free plan
   includes 300 emails/day, plenty for development).
2. Go to **Senders, Domains & Dedicated IPs → Senders** and click **Add a New
   Sender**. Enter a name and an email address you can receive mail at (a
   personal Gmail/Outlook address is fine — you do **not** need to own a
   domain). Brevo emails that address a confirmation link; click it to verify.
3. Go to the gear icon (top right) → **SMTP & API → API Keys** and generate a
   new **v3 API key**. Copy it immediately, it's only shown once.
4. Put that key in `.env` as `BREVO_API_KEY`, and the verified address as
   `BREVO_SENDER_EMAIL`.
5. Running on `localhost` is fine — sending an email is an outgoing request
   from your Django server to Brevo's API, so your site does not need to be
   publicly reachable. (Domain authentication with SPF/DKIM records is
   optional and only improves inbox deliverability for a domain you own — it
   is not required to send.)
