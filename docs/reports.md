# Reports — how they work

This describes `apps/reports/` in plain English. Useful as a viva script: for
each report you can say *what it answers*, *who can see it*, and *the one
Django idea it demonstrates*.

## The shared PDF helper

Every report page can be viewed on-screen **or** downloaded as a PDF, by
adding `?download=pdf` to its URL. Instead of repeating the same "turn this
template into a PDF" code in all 13 views, that logic lives in one function:

`apps/reports/utils.py` → `export_pdf(request, template_name, context, filename)`

- If the URL does **not** have `?download=pdf`, it returns `None` straight
  away — meaning "nothing to download, carry on and show the HTML page".
- If it **does**, it renders the given template with `render_to_string`,
  wraps a `HttpResponse` with the PDF content type, and hands the HTML to
  `xhtml2pdf` (`pisa.CreatePDF`) to turn into a real PDF file.

Every view ends with the same two lines:

```python
pdf_response = export_pdf(request, '<template>_pdf.html', context, '<name>.pdf')
if pdf_response:
    return pdf_response          # a pdf was requested and built — send it

return render(request, '<template>.html', context)   # otherwise, show the normal page
```

So each report's `def` only has to worry about **building the data** — the
"how do I turn this into a downloadable file" part is written once.

Two reports (`doctor_revenue_report`, `appointment_summary_report`) still
have one extra `if` above this, because they can't build a PDF at all until
an admin has picked a doctor — that guard checks for a missing doctor and
redirects with an error message first.

## The 13 report views (`apps/reports/views.py`)

| View function | Question it answers | Who can view it | Main Django idea |
|---|---|---|---|
| `reports_index` | Landing page listing every report | admin, doctor | just `render()`, no data |
| `doctor_revenue_report` | How much has one doctor's appointments collected, and their own cut? | admin, doctor (own only) | looping over a queryset to total up related `payment` fields |
| `appointment_summary_report` | How many of one doctor's appointments are pending/confirmed/cancelled? | admin, doctor (own only) | `.filter(status=...).count()` per status |
| `hospital_revenue_report` | Total money collected hospital-wide, consultations vs pharmacy | admin | looping + adding up amounts by `status`/`method` |
| `department_performance_report` | Appointment count and paid revenue per department | admin | grouping appointments into a plain Python dict, keyed by department |
| `doctors_leaderboard_report` | Every doctor ranked by revenue and take-home pay | admin | same grouping idea, then `list.sort()` |
| `hospital_appointment_status_report` | Hospital-wide appointment status counts + full filterable list | admin | `Paginator` to split a long list into pages |
| `low_stock_report` | Which medicines are at or below their reorder level | admin, pharmacist | Python list comprehension using a model property (`is_low_stock`) |
| `medicine_expiry_report` | Which stock batches are expired or expiring within 30 days | admin, pharmacist | `date.today() + timedelta(...)` for a cutoff date |
| `medicine_sales_report` | Units sold and estimated revenue per medicine | admin, pharmacist | `.values().annotate(Sum(...), Count(...))` — grouping in the database |
| `stock_valuation_report` | How much the current stock is worth | admin, pharmacist | `F('quantity') * F('purchase_price')` inside `Sum()` — doing the multiply in the database |
| `patient_registration_report` | Patients registered in a date range, active/inactive/discharged counts | admin | `Paginator` again, plus `select_related('user')` to avoid extra queries |
| `staff_headcount_report` | Staff counts per department and per role | admin | `.values().annotate(Count('id'))` grouped two different ways |

All 13 use `@login_required` (must be logged in) and `@required_role([...])`
(from `apps/core/utils.py`) to check the user's role before letting them see
the page at all.

## Common pattern across most reports

1. Read `start_date` / `end_date` (and sometimes `department`) from
   `request.GET`.
2. Start with `Model.objects.select_related(...)` (or `.filter(...)`) and
   narrow it down with `.filter(date__gte=start_date)` /
   `.filter(date__lte=end_date)` if those were given.
3. Either loop over the queryset in Python to add up totals, or use
   `.annotate(Sum(...), Count(...))` to let the database do the adding up.
4. Put everything the template needs into one `context` dict.
5. Call `export_pdf(...)` — if a PDF was requested, return it; otherwise
   `render()` the normal HTML page.
