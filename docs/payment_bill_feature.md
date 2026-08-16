# Payment Bill (Email + PDF Download)

This is the reference doc for the payment bill feature, alongside
`docs/notification_feature.md` (which this builds on) and `docs/reports_feature.md`
(whose PDF pattern this reuses). Follow this shape when touching this feature again.

## What this feature does

There are two kinds of bill: the **consultation bill** (the appointment's
department + doctor fee) and the **medicine bill** (the pharmacy order's
prescribed items). Both already had a "payment received" email — this feature
turns those emails into real itemized bills, and adds a "Download Bill (PDF)"
button so the patient can also grab a PDF copy any time from "My Appointments".

No new trigger points were added. The four existing payment moments already
covered every "online or pay at hospital" case:

| Bill | Online | Pay at hospital |
|---|---|---|
| Consultation | `_record_payment()` (booking form) | `confirm_cash_payment()` (reception) |
| Medicine | `pay_medicine_online()` (patient, online) | `pharmacy_order_detail()` "record_payment" action (pharmacist, cash) |

All four still call the same two email functions as before
(`send_appointment_confirmation_email`, `send_medicine_payment_confirmation_email`)
— only what those functions render has changed.

## Bill numbering

No new numbering scheme. Both bills reuse the existing `transaction_ref`
already generated when a payment is marked paid:
- Consultation bill number = `payment.transaction_ref` (e.g. `PAY-000123` / `CASH-000123`).
- Medicine bill number = `order.transaction_ref`.

## The email bills (`apps/appointment/notifications.py`)

- `send_appointment_confirmation_email(appointment)` — now also looks up
  `appointment.payment` and passes `department_fee` (`payment.amount -
  payment.doctor_fee_amount`) and `doctor_fee` (`payment.doctor_fee_amount`)
  into the template, so `emails/appointment/confirmation.html` can show a
  "Payment Bill" section (fee breakdown, total, method, transaction ref, paid
  on, a green "PAID" badge). If there is no payment yet, the section is just
  skipped — the confirmation half of the email still renders fine.
- `send_medicine_payment_confirmation_email(order)` — now builds
  `billed_items`, a list of `{name, quantity, unit_price, subtotal}` dicts (one
  per `PrescriptionItem`), instead of just handing the template the plain
  `prescribed_items` queryset. `emails/pharmacy/medicine_payment_confirmation.html`
  renders that as a real itemized table instead of a bare "Medicine × qty" list.

## The PDF downloads

Same pattern as `apps/reports/views.py` (`doctor_revenue_report`,
`appointment_summary_report`): `render_to_string()` a plain, Bootstrap-free
template, then `xhtml2pdf`'s `pisa.CreatePDF()` writes it straight into an
`HttpResponse(content_type='application/pdf')`. `xhtml2pdf` is imported inside
the view function, not at the top of the file, same as the reports app.

- `download_appointment_bill(request, pk)` (`apps/appointment/views.py`) —
  `@login_required`, looks up the appointment with
  `get_object_or_404(Appointment, pk=pk, patient=request.user)` so a patient
  can only ever download their own bill. Redirects back with a `messages.error`
  if there is no `payment` yet or it isn't `status='paid'`. Renders
  `frontend/appointment/appointment_bill_pdf.html`.
- `download_medicine_bill(request, pk)` — same shape, but for
  `appointment.pharmacy_order` and `order.payment_status == 'paid'`, building
  the same `billed_items` list described above. Renders
  `frontend/appointment/medicine_bill_pdf.html`.
- Both set `Content-Disposition: attachment; filename="bill_<transaction_ref>.pdf"`
  so the browser downloads the file instead of opening it inline.

### URLs (`apps/appointment/urls.py`)

- `/appointment/my/<pk>/bill/appointment.pdf` → `download_appointment_bill`
- `/appointment/my/<pk>/bill/medicine.pdf` → `download_medicine_bill`

### Templates

- `templates/frontend/appointment/appointment_bill_pdf.html`
- `templates/frontend/appointment/medicine_bill_pdf.html`

Both are plain CSS (no Bootstrap, same reason `doctor_revenue_pdf.html` is
separate from its on-screen version — `xhtml2pdf` can't render Bootstrap/flex
layouts), styled as a letterhead-style receipt: hospital name, bill number,
paid date, a "PAID" stamp, billed-to details, an itemized table, and a total.

### Frontend button (`templates/frontend/appointment/my_appointments.html`)

- "Download Bill (PDF)" next to Edit/Cancel in the Appointment Details card,
  shown when `selected_appointment.payment.status == 'paid'`.
- "Download Bill (PDF)" in the Medicine Bill card, shown when
  `pharmacy_order.payment_status == 'paid'`.

No new context variables were needed in `my_appointments()` — the template
reads `selected_appointment.payment` directly through the existing
`OneToOneField(related_name='payment')`, same as everywhere else in the app.
