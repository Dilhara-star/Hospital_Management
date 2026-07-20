# Doctor Hourly Fee + Reports

This is the reference doc for two connected changes: how an appointment's fee
is calculated, and the new "Reports" menu. Follow this shape when touching
either feature again.

## Fee calculation change

Before: `Payment.amount` was just the department's `DepartmentFee`.

Now: `Payment.amount` = `DepartmentFee` (unchanged, still edited on the
"Consultation Fees" page) **+** the assigned doctor's own `hourly_fee` (set by
an admin on the doctor's staff profile). Each doctor can charge a different
rate; the department fee is the hospital's own base charge on top of that.

- `apps/user_management/models.py` — `StaffProfile.hourly_fee`: a doctor's own
  consultation fee. Only meaningful when the profile's role is `doctor`, but
  it lives on `StaffProfile` like `room_number` does, not on a separate model.
- `apps/appointment/models.py` — `Payment.doctor_fee_amount`: a **snapshot**
  of just the doctor's cut, taken at the moment the appointment was paid. This
  is what makes the "Doctor Revenue" report correct even after an admin later
  changes that doctor's rate — the hospital's own share is always derivable
  as `amount - doctor_fee_amount`, so no separate column was needed for it.
- `apps/appointment/views.py::_record_payment` — the one place that computes
  the fee. Uses a small `_doctor_fee(doctor)` helper (same shape as the
  existing `_doctor_room(doctor)` helper) to look up the doctor's rate.
- `templates/frontend/appointment/form.html` — the booking page's live fee
  preview reads **both** `id_department` and `id_doctor` and adds their two
  fees together (`department-fees` and `doctor-fees` JSON blocks).

### Setting a doctor's fee

- Admin: `/user-management/staff/<id>/edit/` → "Employment Details" card →
  "Hourly Fee" field, shown only when editing someone whose role is `doctor`.
- The doctor can see (not edit) their own rate on "My Profile"
  (`templates/dashboard/profile/profile.html`), under their role.

### Seed data

Two data migrations fill in demo numbers on a fresh database, and only ever
touch rows that are still at their default/zero value (never overwrite a
fee staff already configured through the app):
- `apps/user_management/migrations/0006_seed_doctor_hourly_fees.py` — cycles
  demo doctors through `1000, 1500, 2000, 2500`.
- `apps/appointment/migrations/0007_seed_department_fees.py` — sets every
  department to `1500` if it doesn't have a fee row yet.

## Reports menu

Lives inside `apps/appointment` (where `Appointment`/`Payment` already are) —
no new Django app. This first version only has the **doctor's own** reports;
other roles' reports are a future addition.

### Access rules

- `_is_report_staff(user)` / `_require_report_staff(request)` — only `doctor`
  and `admin` roles may open Reports at all (checked in
  `apps/appointment/views.py`, sidebar link hidden for everyone else in
  `templates/dashboard/layouts/sidebar.html`).
- `_resolve_report_doctor(request)` — shared by both report pages (not the
  PDF views, see below). A `doctor` role always gets back `request.user` —
  the `?doctor_id=` query string is ignored so a doctor can't view a
  colleague's report by editing the URL. An `admin` role gets back the
  doctor named by `?doctor_id=`, or **`None`** if they haven't picked one yet.

### Doctor filtering lives on the report page, not the index

`reports_index` is just two cards (Doctor Revenue, Appointment Summary) for
both roles — it no longer lists doctors. Instead, `doctor_revenue.html` and
`appointment_summary.html` each render a "Doctor" `<select>` filter **only
when `request.user.profile.role == 'admin'`**; a doctor never sees it. When
an admin opens a report with no `doctor_id` yet, the view still renders the
page (`doctor` is `None` in the context) so the filter shows, and the
template shows "Select a doctor above..." instead of a data table. The PDF
views (`doctor_revenue_report_pdf` / `appointment_summary_report_pdf`) still
require a resolved doctor — if `None`, they redirect back to the on-screen
report with an error, since there's nothing to put in a PDF yet.

### Views (`apps/appointment/views.py`)

- `reports_index` — landing page, just the two cards.
- `_doctor_revenue_data` / `_appointment_summary_data` — build the report
  data once each (only called once a doctor is known), reused by both the
  on-screen page and the PDF download so the numbers can never drift apart.
- `doctor_revenue_report` / `doctor_revenue_report_pdf` — total collected,
  doctor take-home (`sum(payment.doctor_fee_amount)`), hospital share, and
  the appointment list, for an optional `start_date`/`end_date` range.
- `appointment_summary_report` / `appointment_summary_report_pdf` — counts by
  status (`pending`/`confirmed`/`cancelled`) and the appointment list, same
  date range filter.

### PDF downloads

Built with `xhtml2pdf` (`render_to_string()` a plain, Bootstrap-free template
→ `pisa.CreatePDF()` → `HttpResponse(content_type='application/pdf')`). The
PDF templates (`doctor_revenue_pdf.html`, `appointment_summary_pdf.html`) are
separate from the on-screen ones because `xhtml2pdf` only understands basic
CSS, not Bootstrap.

### URLs (`apps/appointment/urls.py`)

- `/Appointments/reports/` → `reports_index`
- `/Appointments/reports/doctor-revenue/` (+ `/pdf/`) → revenue report
- `/Appointments/reports/appointment-summary/` (+ `/pdf/`) → summary report

### Templates

- `templates/dashboard/report_management/index.html`
- `templates/dashboard/report_management/doctor_revenue.html` /
  `doctor_revenue_pdf.html`
- `templates/dashboard/report_management/appointment_summary.html` /
  `appointment_summary_pdf.html`
- `templates/dashboard/layouts/sidebar.html` — "Reports" nav item, shown only
  for `doctor` / `admin` roles.
