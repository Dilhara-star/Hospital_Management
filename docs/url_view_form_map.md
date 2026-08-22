# URL → Code Line Map

Find a page URL below. It tells you which file and line has the `urls.py` route, the `views.py` function, and the `forms.py` class (if that page uses one).

Format: `URL` → `urls.py line` | `views.py function (line)` | `forms.py class (line)`

## Public site (no `dashboard/` prefix)

App: `apps/frontend/` — urls: [apps/frontend/urls.py](apps/frontend/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/` | [line 8](apps/frontend/urls.py#L8) | `frontend_index` [line 21](apps/frontend/views.py#L21) | — |
| `/profile/` | [line 9](apps/frontend/urls.py#L9) | `profile_view` [line 60](apps/frontend/views.py#L60) | `ProfileDetailsForm` [line 6](apps/frontend/forms.py#L6), `ProfilePictureForm` [line 37](apps/frontend/forms.py#L37), `ChangePasswordForm` [line 42](apps/frontend/forms.py#L42) |
| `/patient-portal/` | [line 10](apps/frontend/urls.py#L10) | `patient_portal` [line 112](apps/frontend/views.py#L112) | — |
| `/doctors/` | [line 11](apps/frontend/urls.py#L11) | `doctor_list` [line 28](apps/frontend/views.py#L28) | — |
| `/doctors/<pk>/` | [line 12](apps/frontend/urls.py#L12) | `doctor_detail` [line 53](apps/frontend/views.py#L53) | — |

App: `apps/core/` — urls: [apps/core/urls.py](apps/core/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/core/about-us` | [line 7](apps/core/urls.py#L7) | `about_us` [line 5](apps/core/views.py#L5) | — |
| `/core/terms-of-service` | [line 8](apps/core/urls.py#L8) | `terms_of_service` [line 10](apps/core/views.py#L10) | — |
| `/core/privacy-policy` | [line 9](apps/core/urls.py#L9) | `privacy_policy` [line 15](apps/core/views.py#L15) | — |

App: `apps/contact/` (public part) — urls: [apps/contact/urls.py](apps/contact/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/contact/index/` | [line 6](apps/contact/urls.py#L6) | `contact_us_index` [line 13](apps/contact/views.py#L13) | — |
| `/contact/add_contact/` | [line 7](apps/contact/urls.py#L7) | `add_contact` [line 19](apps/contact/views.py#L19) | `ContactForm` [line 6](apps/contact/forms.py#L6) |

App: `apps/appointment/` (public part) — urls: [apps/appointment/urls.py](apps/appointment/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/Appointment/` | [line 8](apps/appointment/urls.py#L8) | `appointment_form` [line 358](apps/appointment/views.py#L358) | — |
| `/Appointment/my/` | [line 9](apps/appointment/urls.py#L9) | `my_appointments` [line 419](apps/appointment/views.py#L419) | — |
| `/Appointment/my/<pk>/` | [line 10](apps/appointment/urls.py#L10) | `my_appointments` [line 419](apps/appointment/views.py#L419) | — |
| `/Appointment/payments/` | [line 11](apps/appointment/urls.py#L11) | `payment_history` [line 460](apps/appointment/views.py#L460) | — |
| `/Appointment/my/<pk>/bill/appointment.pdf` | [line 12](apps/appointment/urls.py#L12) | `download_appointment_bill` [line 479](apps/appointment/views.py#L479) | — |
| `/Appointment/edit_appointment/<pk>/` | [line 13](apps/appointment/urls.py#L13) | `edit_appointment` [line 506](apps/appointment/views.py#L506) | — |
| `/Appointment/cancel/<pk>/` | [line 14](apps/appointment/urls.py#L14) | `cancel_appointment` [line 528](apps/appointment/views.py#L528) | — |
| `/Appointment/refund/<pk>/` | [line 15](apps/appointment/urls.py#L15) | `refund_appointment` [line 562](apps/appointment/views.py#L562) | — |
| `/Appointment/refund/<pk>/process/` | [line 18](apps/appointment/urls.py#L18) | `appointment_refund_process_by_patient` [line 583](apps/appointment/views.py#L583) | — |

App: `apps/pharmacy/` (public part) — urls: [apps/pharmacy/urls.py](apps/pharmacy/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/pharmacy/my/<pk>/pay-medicine/` | [line 6](apps/pharmacy/urls.py#L6) | `pay_medicine_online` [line 232](apps/pharmacy/views.py#L232) | — |
| `/pharmacy/my/<pk>/bill/medicine.pdf` | [line 7](apps/pharmacy/urls.py#L7) | `download_medicine_bill` [line 250](apps/pharmacy/views.py#L250) | — |

## Dashboard (staff) pages — all start with `/dashboard/`

App: `apps/dashboard/` — urls: [apps/dashboard/urls.py](apps/dashboard/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/` | [line 7](apps/dashboard/urls.py#L7) | `dashboard_index` [line 39](apps/dashboard/views.py#L39) | — |
| `/dashboard/register/` | [line 8](apps/dashboard/urls.py#L8) | `register_view` [line 132](apps/dashboard/views.py#L132) | `PatientSignupForm` [line 5](apps/dashboard/forms.py#L5) |
| `/dashboard/profile/` | [line 9](apps/dashboard/urls.py#L9) | `dashboard_profile` [line 68](apps/dashboard/views.py#L68) | — |

App: `apps/user_management/` — mounted at `dashboard/users/` — urls: [apps/user_management/urls.py](apps/user_management/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/users/login/` | [line 8](apps/user_management/urls.py#L8) | `login_view` [line 43](apps/user_management/views.py#L43) | — |
| `/dashboard/users/logout/` | [line 9](apps/user_management/urls.py#L9) | `logout_view` [line 71](apps/user_management/views.py#L71) | — |
| `/dashboard/users/forgot-password/` | [line 10](apps/user_management/urls.py#L10) | `forgot_password_view` [line 79](apps/user_management/views.py#L79) | `ForgotPasswordForm` [line 12](apps/user_management/forms.py#L12) |
| `/dashboard/users/reset-password/<uidb64>/<token>/` | [line 11](apps/user_management/urls.py#L11) | `reset_password_confirm_view` [line 108](apps/user_management/views.py#L108) | `SetNewPasswordForm` [line 17](apps/user_management/forms.py#L17) |
| `/dashboard/users/patients/` | [line 14](apps/user_management/urls.py#L14) | `patient_user_list` [line 142](apps/user_management/views.py#L142) | — |
| `/dashboard/users/patients/add/` | [line 15](apps/user_management/urls.py#L15) | `patient_add` [line 153](apps/user_management/views.py#L153) | `PatientCreateForm` [line 38](apps/user_management/forms.py#L38) |
| `/dashboard/users/patients/<id>/edit/` | [line 16](apps/user_management/urls.py#L16) | `patient_edit` [line 208](apps/user_management/views.py#L208) | `PatientEditForm` [line 102](apps/user_management/forms.py#L102) |
| `/dashboard/users/patients/<id>/detail/` | [line 17](apps/user_management/urls.py#L17) | `patient_detail` [line 269](apps/user_management/views.py#L269) | — |
| `/dashboard/users/patients/<id>/delete/` | [line 18](apps/user_management/urls.py#L18) | `patient_delete` [line 281](apps/user_management/views.py#L281) | — |
| `/dashboard/users/staff/` | [line 21](apps/user_management/urls.py#L21) | `staff_user_list` [line 302](apps/user_management/views.py#L302) | — |
| `/dashboard/users/staff/add/` | [line 22](apps/user_management/urls.py#L22) | `staff_add` [line 312](apps/user_management/views.py#L312) | `StaffCreateForm` [line 179](apps/user_management/forms.py#L179) |
| `/dashboard/users/staff/<id>/edit/` | [line 23](apps/user_management/urls.py#L23) | `staff_edit` [line 354](apps/user_management/views.py#L354) | `StaffEditForm` [line 227](apps/user_management/forms.py#L227) |
| `/dashboard/users/staff/<id>/detail/` | [line 24](apps/user_management/urls.py#L24) | `staff_detail` [line 417](apps/user_management/views.py#L417) | — |
| `/dashboard/users/staff/<id>/delete/` | [line 25](apps/user_management/urls.py#L25) | `staff_delete` [line 438](apps/user_management/views.py#L438) | — |
| `/dashboard/users/doctor-rooms/` | [line 28](apps/user_management/urls.py#L28) | `doctor_room_list` [line 459](apps/user_management/views.py#L459) | — |

App: `apps/supplier/` — mounted at `dashboard/supplier/` — urls: [apps/supplier/urls.py](apps/supplier/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/supplier/` | [line 6](apps/supplier/urls.py#L6) | `supplier_list` [line 17](apps/supplier/views.py#L17) | — |
| `/dashboard/supplier/add/` | [line 7](apps/supplier/urls.py#L7) | `supplier_add` [line 25](apps/supplier/views.py#L25) | `SupplierForm` [line 7](apps/supplier/forms.py#L7) |
| `/dashboard/supplier/<pk>/edit/` | [line 8](apps/supplier/urls.py#L8) | `supplier_edit` [line 49](apps/supplier/views.py#L49) | `SupplierForm` [line 7](apps/supplier/forms.py#L7) |
| `/dashboard/supplier/<pk>/detail/` | [line 9](apps/supplier/urls.py#L9) | `supplier_detail` [line 71](apps/supplier/views.py#L71) | — |
| `/dashboard/supplier/<pk>/delete/` | [line 10](apps/supplier/urls.py#L10) | `supplier_delete` [line 79](apps/supplier/views.py#L79) | — |

App: `apps/stock/` — mounted at `dashboard/stock/` — urls: [apps/stock/urls.py](apps/stock/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/stock/medicines/` | [line 7](apps/stock/urls.py#L7) | `medicine_list` [line 19](apps/stock/views.py#L19) | — |
| `/dashboard/stock/medicines/add/` | [line 8](apps/stock/urls.py#L8) | `medicine_add` [line 27](apps/stock/views.py#L27) | `MedicineForm` [line 7](apps/stock/forms.py#L7) |
| `/dashboard/stock/medicines/<pk>/edit/` | [line 9](apps/stock/urls.py#L9) | `medicine_edit` [line 49](apps/stock/views.py#L49) | `MedicineForm` [line 7](apps/stock/forms.py#L7) |
| `/dashboard/stock/medicines/<pk>/detail/` | [line 10](apps/stock/urls.py#L10) | `medicine_detail` [line 71](apps/stock/views.py#L71) | — |
| `/dashboard/stock/medicines/<pk>/delete/` | [line 11](apps/stock/urls.py#L11) | `medicine_delete` [line 80](apps/stock/views.py#L80) | — |
| `/dashboard/stock/batches/` | [line 14](apps/stock/urls.py#L14) | `stock_list` [line 95](apps/stock/views.py#L95) | — |
| `/dashboard/stock/batches/add/` | [line 15](apps/stock/urls.py#L15) | `stock_add` [line 103](apps/stock/views.py#L103) | `MedicineStockForm` [line 14](apps/stock/forms.py#L14) |
| `/dashboard/stock/batches/<pk>/edit/` | [line 16](apps/stock/urls.py#L16) | `stock_edit` [line 130](apps/stock/views.py#L130) | `MedicineStockForm` [line 14](apps/stock/forms.py#L14) |
| `/dashboard/stock/batches/<pk>/detail/` | [line 17](apps/stock/urls.py#L17) | `stock_detail` [line 157](apps/stock/views.py#L157) | — |
| `/dashboard/stock/batches/<pk>/delete/` | [line 18](apps/stock/urls.py#L18) | `stock_delete` [line 165](apps/stock/views.py#L165) | — |

App: `apps/reports/` — mounted at `dashboard/reports/` — urls: [apps/reports/urls.py](apps/reports/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/reports/` | [line 5](apps/reports/urls.py#L5) | `reports_index` [line 16](apps/reports/views.py#L16) | — |
| `/dashboard/reports/doctor-revenue/` | [line 6](apps/reports/urls.py#L6) | `doctor_revenue_report` [line 23](apps/reports/views.py#L23) | — |
| `/dashboard/reports/appointment-summary/` | [line 7](apps/reports/urls.py#L7) | `appointment_summary_report` [line 82](apps/reports/views.py#L82) | — |
| `/dashboard/reports/hospital-revenue/` | [line 8](apps/reports/urls.py#L8) | `hospital_revenue_report` [line 133](apps/reports/views.py#L133) | — |
| `/dashboard/reports/department-performance/` | [line 9](apps/reports/urls.py#L9) | `department_performance_report` [line 215](apps/reports/views.py#L215) | — |
| `/dashboard/reports/doctors-leaderboard/` | [line 10](apps/reports/urls.py#L10) | `doctors_leaderboard_report` [line 271](apps/reports/views.py#L271) | — |
| `/dashboard/reports/appointment-status/` | [line 11](apps/reports/urls.py#L11) | `hospital_appointment_status_report` [line 330](apps/reports/views.py#L330) | — |

App: `apps/appointment/` (staff part) — mounted at `dashboard/appointments/` — urls: [apps/appointment/urls.py](apps/appointment/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/appointments/index/` | [line 25](apps/appointment/urls.py#L25) | `appointment_index` [line 109](apps/appointment/views.py#L109) | — |
| `/dashboard/appointments/add/` | [line 26](apps/appointment/urls.py#L26) | `appointment_add` [line 133](apps/appointment/views.py#L133) | `StaffAppointmentForm` [line 26](apps/appointment/forms.py#L26) |
| `/dashboard/appointments/view/<pk>/` | [line 27](apps/appointment/urls.py#L27) | `appointment_view` [line 121](apps/appointment/views.py#L121) | — |
| `/dashboard/appointments/edit/<pk>/` | [line 28](apps/appointment/urls.py#L28) | `appointment_edit` [line 173](apps/appointment/views.py#L173) | `AppointmentEditForm` [line 53](apps/appointment/forms.py#L53) |
| `/dashboard/appointments/delete/<pk>/` | [line 29](apps/appointment/urls.py#L29) | `appointment_delete` [line 246](apps/appointment/views.py#L246) | — |
| `/dashboard/appointments/confirm-payment/<pk>/` | [line 30](apps/appointment/urls.py#L30) | `confirm_cash_payment` [line 260](apps/appointment/views.py#L260) | — |
| `/dashboard/appointments/fees/` | [line 31](apps/appointment/urls.py#L31) | `fee_index` [line 281](apps/appointment/views.py#L281) | — |
| `/dashboard/appointments/payments/` | [line 32](apps/appointment/urls.py#L32) | `payment_index` [line 306](apps/appointment/views.py#L306) | — |
| `/dashboard/appointments/payments/<pk>/refund/` | [line 33](apps/appointment/urls.py#L33) | `payment_refund` [line 339](apps/appointment/views.py#L339) | `PaymentForm` [line 45](apps/appointment/forms.py#L45) |

Note: `AppointmentForm` [line 10](apps/appointment/forms.py#L10) exists in forms.py but is not wired to a view right now.

App: `apps/pharmacy/` (staff part) — mounted at `dashboard/pharmacy/` — urls: [apps/pharmacy/urls.py](apps/pharmacy/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/pharmacy/queue/` | [line 12](apps/pharmacy/urls.py#L12) | `pharmacy_queue` [line 136](apps/pharmacy/views.py#L136) | — |
| `/dashboard/pharmacy/<pk>/` | [line 13](apps/pharmacy/urls.py#L13) | `pharmacy_order_detail` [line 154](apps/pharmacy/views.py#L154) | — |
| `/dashboard/pharmacy/prescribe/<pk>/search/` | [line 14](apps/pharmacy/urls.py#L14) | `appointment_pharmacy_search` [line 103](apps/pharmacy/views.py#L103) | — |
| `/dashboard/pharmacy/prescribe/<pk>/remove-medicine/<item_pk>/` | [line 15](apps/pharmacy/urls.py#L15) | `prescription_item_delete` [line 116](apps/pharmacy/views.py#L116) | — |

App: `apps/contact/` (staff part) — mounted at `dashboard/contact/` — urls: [apps/contact/urls.py](apps/contact/urls.py)

| URL | urls.py | views.py | forms.py |
|---|---|---|---|
| `/dashboard/contact/list/` | [line 12](apps/contact/urls.py#L12) | `view_inquiries` [line 43](apps/contact/views.py#L43) | — |
| `/dashboard/contact/view_inquiry/<id>/` | [line 13](apps/contact/urls.py#L13) | `view_inquiry` [line 51](apps/contact/views.py#L51) | — |
| `/dashboard/contact/mark_solved/<id>/` | [line 14](apps/contact/urls.py#L14) | `mark_inquiry_solved` [line 59](apps/contact/views.py#L59) | — |

## Root file

- [Hospital_Management/urls.py](Hospital_Management/urls.py) — this file plugs every app's `urls.py` into the site. Line numbers above are inside each app's own `urls.py`, not this file.

## Tip

If line numbers shift after you edit a file, just search the function or class name — the line count moves but the name stays the same.
