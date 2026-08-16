# Additional Email Notifications

This doc covers the emails added on top of the original appointment
confirmation feature (see `docs/notification_feature.md` for the base
pattern: Brevo's transactional email API, one function per email in a
per-app `notifications.py`, called from `views.py` right after the
triggering model is saved, wrapped in `try/except requests.RequestException`
so a Brevo outage never breaks a page).

## Bug fix

`send_appointment_confirmation_email_admin` (`apps/appointment/notifications.py`)
used to read a bare `ADMIN_NOTIFY_EMAIL` name that was never imported, which
crashed with an uncaught `NameError` every time an appointment was confirmed
with payment already received. Fixed to read `settings.ADMIN_NOTIFY_EMAIL`,
same as every other admin-facing email in the file.

## Contact Us → admin, and resolved → sender (`apps/contact`)

- `send_contact_inquiry_admin_email(inquiry)` — sent from `add_contact()`
  right after a new `Contact_us` row is saved. Goes to `ADMIN_NOTIFY_EMAIL`.
- `send_contact_resolved_email(inquiry)` — sent from the new
  `mark_inquiry_solved()` view/URL (`contact/mark_solved/<id>/`), which sets
  `status='solved'` and emails the original sender. The dashboard's "Mark as
  Solved" button now posts to this view instead of only toggling CSS; while
  wiring it up, a pre-existing bug was also fixed where every inquiry card
  shared the same hardcoded DOM id (`card-1`/`badge-1`), so only the first
  card in the list ever actually worked.
- `Contact_us` is now registered in `apps/contact/admin.py` (it wasn't
  before).

## Doctor assignment and pharmacy dispense (`apps/appointment`)

- `send_doctor_assignment_email(appointment)` — sent whenever a doctor is
  newly assigned or changed on an appointment: on new bookings
  (`appointment_form`, `appointment_add`) and on the staff edit form
  (`appointment_edit`, only when the doctor actually changed).
- `send_medicine_dispensed_email(order)` — sent from `pharmacy_order_detail()`
  right after a `PharmacyOrder` is marked `dispensed`, so the patient knows
  to pay before the existing `send_medicine_payment_confirmation_email`
  (which only fires once payment is recorded).
- `appointment_edit()` also now sends the existing
  `send_appointment_cancellation_email` when staff cancel an appointment
  through the status dropdown — previously only the patient's own
  self-cancel and refund flows emailed on cancellation.

## Stock and insurance expiry digests (`apps/inventory`, `apps/user_management`)

No task scheduler (Celery, django-crontab, etc.) exists in this project, so
these are plain Django management commands, run by hand or scheduled with
Windows Task Scheduler:

- `python manage.py send_expiry_alerts` — emails `ADMIN_NOTIFY_EMAIL` one
  digest listing every `MedicineStock` batch that is expired or expiring
  within 30 days (using the model's existing `is_expired` /
  `is_expiring_soon` properties). Only sends if there's something to report.
- `python manage.py send_insurance_reminders` — emails every patient whose
  `PatientProfile.insurance_expiry` falls within the next 30 days.

## Password reset (`apps/dashboard`)

No password reset flow existed anywhere in the project before this. Added
as plain function-based views (not Django's built-in class-based
`PasswordResetView`, to stay consistent with this project's FBV-only rule
and its Brevo-only email sending):

- `forgot_password_view` (`/dashboard/forgot-password/`) — looks up the
  account by email, and if found, builds a reset link using
  `django.contrib.auth.tokens.default_token_generator` plus the account's
  base64-encoded id. No new database field is needed — the token is
  verified against the account's current password hash, so it naturally
  stops working once used or once the password changes. Always shows the
  same success message, whether or not the email matched an account.
- `reset_password_confirm_view` (`/dashboard/reset-password/<uidb64>/<token>/`)
  — verifies the token, then lets the user set a new password.
- `send_password_reset_email(user, reset_link)` in the new
  `apps/dashboard/notifications.py`.
- A "Forgot Password?" link was added to `templates/dashboard/auth/login.html`.

## Discharge notice (`apps/user_management`)

- `send_patient_discharge_email(patient_user)` — sent from `patient_edit()`
  when a patient's status is changed to `discharged` (there is no separate
  "discharge" view; status is just one option on the existing edit form).

## Supplier welcome (`apps/inventory`)

- `send_supplier_welcome_email(supplier)` — sent from `supplier_add()` right
  after a new `Supplier` is saved.

## Setup

Uses the same `.env` Brevo settings as the original feature — no new
environment variables were added:

```
BREVO_API_KEY=your-brevo-api-key-here
BREVO_SENDER_EMAIL=your-verified-sender@example.com
BREVO_SENDER_NAME=Medi Plus
ADMIN_NOTIFY_EMAIL=admin-inbox@example.com
```
