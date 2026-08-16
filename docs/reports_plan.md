# Reports Expansion Plan

Reference doc for growing `apps/reports` beyond the two doctor/admin reports
built in [reports_feature.md](reports_feature.md) ("other roles' reports are
a future addition" — this is that addition). Follow this shape when building
any report from this list.

## Scope

Every report below is built only from fields that already exist on a model
today (see "Models used" per report). Nothing here needs new columns.
**Customer-facing roles (`patient`, `user`) are out of scope** — they use the
frontend patient portal, not the staff dashboard, and have no report needs.

Roles covered, and what each can already do in the app today (from the
`required_role([...])` checks currently in the code):

| Role | Today's access |
|---|---|
| `admin` | Everything — patients, staff, appointments, fees, pharmacy counter, suppliers, inventory, contact inquiries, reports. |
| `doctor` | Own appointments, pharmacy catalog search, own reports (Doctor Revenue, Appointment Summary). |
| `receptionist` | Appointments (view/add/edit/delete/confirm payment), patients (view/add/edit/delete), fees, doctor rooms. |
| `pharmacist` | Pharmacy catalog search, pharmacy counter (dispense + collect payment), medicine inventory. |
| `nurse` | Appointments (view/add/edit) only. No patient, staff, or inventory access today. |
| `lab_technician` | Defined as a role choice, but **no view or model uses it anywhere in the codebase yet.** No lab test model exists (no test type, result, or status fields on anything). |

Because of that last row, Lab Technician gets no reports in this plan — there
is nothing in the database yet that belongs to them. It's called out as a
gap, not silently skipped, in case a future `LabTest` model is wanted later.

## Report catalog, by role

Each entry: purpose, the models/fields it reads, and any filter it should
take (matching the existing `start_date`/`end_date` + role-scoped pattern
from `doctor_revenue_report`).

### Admin (hospital-wide, every report below is also visible to admin)

1. **Hospital Revenue Report** — total income across consultations *and*
   pharmacy, by date range, split by payment method (`online`/`cash`) and
   status (`paid`/`pending`/`refunded`). *Models:* `Payment`, `PharmacyOrder`.
2. **Department Performance Report** — appointment count and revenue per
   `Appointment.department`, using `DepartmentFee` as the base rate. Surfaces
   which departments are busiest/most profitable. *Models:* `Appointment`,
   `DepartmentFee`, `Payment`.
3. **All-Doctors Revenue Leaderboard** — the existing Doctor Revenue report,
   widened from "pick one doctor" to a comparison table (take-home, hospital
   share, appointment count per doctor). *Models:* `Appointment`, `Payment`,
   `StaffProfile.hourly_fee`.
4. **Hospital-wide Appointment Status Report** — pending/confirmed/cancelled
   counts and trend over a date range, across every doctor and department
   (today's Appointment Summary report is per-doctor only). *Models:*
   `Appointment`.
5. **Patient Registration Report** — new patients over time
   (`registered_date`), status split (`active`/`inactive`/`discharged`),
   and demographics (`gender`, `blood_type`, age from `date_of_birth`).
   *Models:* `PatientProfile`, `UserProfile`.
6. **Staff Directory Report** — headcount by department/employment
   type/shift, hire-date tenure. *Models:* `StaffProfile`.
7. **Pharmacy Revenue Report** — completed vs pending `PharmacyOrder`
   totals, by payment method and date. *Models:* `PharmacyOrder`.
8. **Medicine Stock & Valuation Report** — current stock per medicine
   (`Medicine.total_quantity`), stock value (`quantity × price`), and a
   low-stock list (`Medicine.is_low_stock`). *Models:* `Medicine`,
   `MedicineStock`.
9. **Expiry Report** — batches already expired vs expiring within 30 days
   (`MedicineStock.is_expired` / `is_expiring_soon`), batch/supplier detail
   for pulling stock off the shelf. *Models:* `MedicineStock`.
10. **Supplier Purchase Report** — stock received and purchase value per
    supplier, active/inactive status. *Models:* `Supplier`, `MedicineStock`.
11. **Most-Prescribed Medicines Report** — `PrescriptionItem` grouped by
    medicine and summed by quantity, over a date range — informs reordering
    and formulary decisions. *Models:* `PrescriptionItem`.
12. **Refunds Report** — every `Payment` with `status='refunded'`, count and
    amount, linked back to the cancelled appointment. *Models:* `Payment`,
    `Appointment`.
13. **Contact Inquiries Report** — pending vs solved counts and volume over
    time from the public contact form. *Models:* `Contact_us`.

### Doctor (own data only, same scoping as the existing two reports)

14. **My Revenue Report** — *already built.*
15. **My Appointment Summary Report** — *already built.*
16. **My Patient List Report** — distinct patients this doctor has seen,
    with visit count and last-visit date (`Appointment.patient`, filtered to
    `doctor=self`). *Models:* `Appointment`.
17. **My Prescriptions Report** — `PrescriptionItem` rows for this doctor's
    own appointments, grouped by medicine or by date — a review of their own
    prescribing pattern. *Models:* `PrescriptionItem`, `Appointment`.

### Receptionist (front-desk / operational)

18. **Appointment Schedule Report** — appointments for a chosen date/range,
    filterable by doctor/department/status — the front-desk day sheet.
    *Models:* `Appointment`. *(Shared with admin and nurse, read-only for
    nurse — see below.)*
19. **Payment Collection Report** — cash vs online payments taken, for
    daily till reconciliation. *Models:* `Payment`.
20. **Pending Payments Report** — appointments where `Payment.status =
    'pending'`, to chase up patients before/after their visit. *Models:*
    `Payment`, `Appointment`.
21. **Cancelled Appointments Report** — cancellation volume/trend and which
    of those still owe a refund. *Models:* `Appointment`, `Payment`.
22. **Patient Registration Report** — *shared with admin (#5)* — receptionist
    is the one usually entering these, so same report, same access.

### Pharmacist (pharmacy counter / inventory)

23. **Dispensing Log Report** — orders this pharmacist personally dispensed
    (`PharmacyOrder.dispensed_by = self`), with timestamps — an
    accountability log. *Models:* `PharmacyOrder`.
24. **Pending Dispense Queue Report** — `PharmacyOrder.status='pending'`
    (prescribed, not yet given out) — the operational worklist, exportable
    as a report on top of the existing live queue page. *Models:*
    `PharmacyOrder`.
25. **Medicine Stock Report** — *shared with admin (#8).*
26. **Expiry Report** — *shared with admin (#9).*
27. **Pharmacy Revenue Report** — *shared with admin (#7),* scoped to "my
    till" (`dispensed_by=self`) as well as the hospital-wide total.
28. **Supplier Purchase Report** — *shared with admin (#10)* — helps the
    pharmacist decide what/who to reorder from.

### Nurse (limited by what the role can see today)

29. **Appointment Schedule Report** — *shared with receptionist (#18),*
    read-only — nurses can already view/add/edit appointments, so a
    schedule view fits their existing access without a permission change.

No other nurse report is possible from current models — there's no vitals,
nursing-note, or ward-assignment model. If nursing-specific reports are
wanted later (e.g. a shift handover sheet), that needs a new model first,
same as lab technician above.

## Phased build plan

Each phase reuses the exact shape from `apps/reports` today: one
function-based view per report in `apps/reports/views.py`, `@login_required`
+ `@required_role([...])`, a plain HTML template under
`templates/dashboard/report_management/`, and a `?download=pdf` branch in
the same view using `xhtml2pdf` (no separate PDF-only views). Long tables get
`Paginator`; every queryset that loops over a related object gets
`select_related`/`prefetch_related` first.

- **Phase 1 — Admin core financials: BUILT.** #1 Hospital Revenue, #2
  Department Performance, #3 All-Doctors Leaderboard, #4 Hospital-wide
  Appointment Status. All four are `@required_role(['admin'], ...)` — a
  doctor still only sees their own two reports on `reports_index`.
  - `apps/reports/views.py` — `hospital_revenue_report`,
    `department_performance_report`, `doctors_leaderboard_report`,
    `hospital_appointment_status_report`. Same shape as the two original
    reports: one view per report, `?download=pdf` branch inside it.
  - `apps/reports/urls.py` — `/reports/hospital-revenue/`,
    `/reports/department-performance/`, `/reports/doctors-leaderboard/`,
    `/reports/appointment-status/`.
  - Templates: `hospital_revenue.html` / `_pdf.html`,
    `department_performance.html` / `_pdf.html`,
    `doctors_leaderboard.html` / `_pdf.html`,
    `appointment_status.html` / `_pdf.html`, all under
    `templates/dashboard/report_management/`.
  - `department_performance_report` and `doctors_leaderboard_report` each
    fetch their base queryset **once**, then bucket rows into a plain
    Python dict keyed by department code / doctor id — avoids one query per
    department or per doctor while staying a simple `for` loop, no
    `annotate()`/`Sum()` needed.
  - `hospital_appointment_status_report` is the one report so far that
    needs `Paginator` (25 rows/page) — it has no doctor scope, so its list
    can be the longest. The PDF branch still renders the **full**
    unpaginated queryset, since a downloaded report shouldn't be missing
    rows.
  - `reports_index.html` gained a "Hospital-Wide" card row, wrapped in
    `{% if request.user.profile.role == 'admin' %}` — a doctor's index page
    is unchanged.
  - **Fixed: PDF downloads were 500ing on this dev machine**, all six
    reports, old and new alike. Cause: `xhtml2pdf` depends on `svglib`
    (for embedding SVG images in a PDF — a feature none of these report
    templates use), which pulls in `rlPyCairo`, which needs a native
    `cairo` DLL this Windows machine doesn't have. `import rlPyCairo`
    doesn't raise a plain `ImportError` when that DLL is missing — it
    raises `OSError` deep inside `cairocffi`, and reportlab's own backend
    picker only catches `ImportError`, so the whole `reportlab.graphics
    .renderPM` module (and everything importing it, including
    `xhtml2pdf`) crashed on import. Fixed by uninstalling `rlPyCairo` and
    `cairocffi` (`pip uninstall -y rlPyCairo cairocffi`) — with the
    package gone entirely, `import rlPyCairo` now raises a clean
    `ImportError`, which both reportlab's backend picker *and*
    `xhtml2pdf`'s own already-written `except ImportError` both handle
    correctly. No code changes were needed, only removing the two broken
    packages. Verified all six `?download=pdf` endpoints now return real
    PDFs with correct report data (checked by extracting text from the
    generated PDF). See the comment block at the bottom of
    `requirements.txt` — a fresh `pip install -r requirements.txt` will
    pull `rlPyCairo` back in as a transitive dependency and reintroduce
    this exact crash, so the uninstall step has to be repeated after any
    fresh install on a Windows machine without a cairo runtime.
- **Phase 2 — Admin people & pharmacy:** #5 Patient Registration, #6 Staff
  Directory, #7 Pharmacy Revenue, #11 Most-Prescribed Medicines, #13 Contact
  Inquiries, #12 Refunds.
- **Phase 3 — Inventory:** #8 Medicine Stock & Valuation, #9 Expiry, #10
  Supplier Purchase. Shared by admin + pharmacist from day one.
- **Phase 4 — Receptionist:** #18 Appointment Schedule, #19 Payment
  Collection, #20 Pending Payments, #21 Cancelled Appointments. New
  `required_role` entries for `receptionist` on `apps/reports/views.py`.
- **Phase 5 — Doctor extras + Pharmacist + Nurse:** #16 My Patient List, #17
  My Prescriptions, #23 Dispensing Log, #24 Pending Dispense Queue, plus
  wiring `nurse`/`pharmacist` into the shared reports from earlier phases.
- **Phase 6 (future, not scheduled) — Lab Technician:** blocked on a new
  `LabTest` model; out of scope until that's requested.

### Sidebar / access changes needed

`templates/dashboard/layouts/sidebar.html` currently shows "Reports" only to
`doctor`/`admin`. From Phase 4 onward it needs to show for `receptionist`,
`pharmacist`, and `nurse` too, and `reports_index` needs its report cards
filtered per role (same idea as the doctor-vs-admin dropdown split already
on `doctor_revenue.html`).
