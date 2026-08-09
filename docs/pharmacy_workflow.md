# Pharmacy Dispensing & Payment Workflow

This is the reference doc for the pharmacy counter feature, alongside the two PDF
guides in the project root. Follow this shape when touching this feature again.

## What this feature does

1. A doctor prescribes medicine on an appointment (already existed — the pharmacy
   section on the doctor's `appointment_edit` page, adding `PrescriptionItem` rows).
2. A pharmacist opens the Pharmacy Counter, sees the prescription, and **dispenses**
   the medicine (hands it over in person). This is the moment stock is deducted.
3. Payment is recorded — either the pharmacist marks cash received, or the patient
   pays online themselves from their "My Appointments" page.
4. Once the medicine is dispensed **and** paid for, the pharmacist marks the order
   **completed**.

## Models

- `apps/inventory/models.py` — `Medicine.price`: the selling price per unit charged
  to the patient (separate from `MedicineStock.purchase_price`, which is what the
  hospital paid the supplier).
- `apps/appointment/models.py` — `PharmacyOrder`: one row per appointment that has
  prescribed medicine. Holds `status` (`pending` / `dispensed` / `completed`),
  `payment_method` / `payment_status` (same shape as the existing `Payment` model
  used for the consultation fee), `total_amount`, and who/when it was dispensed,
  paid, and completed.

A `PharmacyOrder` row is created lazily (`get_or_create`) the first time a
pharmacist opens the order detail page — there is no signal on `PrescriptionItem`.

## Status flow

```
pending  --[pharmacist clicks "Dispense Medicine"]-->  dispensed
                                                          |
                          [pharmacist confirms cash] or [patient pays online]
                                                          v
                                              dispensed, payment_status = paid
                                                          |
                                     [pharmacist clicks "Mark as Completed"]
                                                          v
                                                     completed
```

Dispensing is the point stock actually leaves the shelf: for each prescribed item,
`apps/appointment/views.py::pharmacy_order_detail` loops the medicine's stock
batches (soonest-expiry-first, same ordering `MedicineStock` already uses) and
takes from them one batch at a time with `select_for_update()` + `F('quantity') - take`,
inside `transaction.atomic()` — the same stock-safety pattern used elsewhere in
this project.

## Views (`apps/appointment/views.py`)

- `pharmacy_queue` — list of appointments with prescribed medicine, not yet
  completed. Pharmacist/admin only (`_is_pharmacist`).
- `pharmacy_order_detail` — one appointment's order. Dispatches on
  `request.POST.get('action')`: `dispense`, `record_payment`, `complete`.
- `pay_medicine_online` — patient-only, POST-only. Lets the patient mark their own
  medicine bill as paid online (simulated, same style as the existing consultation
  fee's online payment — no real payment gateway).

## URLs (`apps/appointment/urls.py`)

- `/appointment/pharmacy/` → `pharmacy_queue`
- `/appointment/pharmacy/<pk>/` → `pharmacy_order_detail` (`pk` is the appointment id)
- `/appointment/my/<pk>/pay-medicine/` → `pay_medicine_online`

## Templates

- `templates/dashboard/pharmacy_management/queue.html` — pharmacist's list page.
- `templates/dashboard/pharmacy_management/order_detail.html` — one order: patient
  info, prescribed items with unit price + line total + grand total, and the three
  action buttons (each only shown when its status guard is met).
- `templates/frontend/appointment/my_appointments.html` — "Medicine Bill" card
  added under the existing "Prescription" card, with the patient's "Pay Online"
  button.
- `templates/dashboard/layouts/sidebar.html` — "Pharmacy Counter" nav item, shown
  only for `pharmacist` / `admin` roles.
