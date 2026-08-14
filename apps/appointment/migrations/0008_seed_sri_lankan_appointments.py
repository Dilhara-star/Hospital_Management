import random  # used to pick random doctors, dates, statuses etc
from datetime import date, timedelta  # date math for appointment dates

from django.db import migrations  # base tools for writing a migration
from django.utils import timezone  # used to stamp "paid at" / "dispensed at" times

# the 8 fixed one-hour appointment slots used across the whole app
TIME_SLOTS = [
    '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
    '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00',
]

# realistic looking LKR consultation fee for each appointment department
DEPARTMENT_FEES = {
    'general': 1000, 'cardiology': 3000, 'neurology': 3500, 'orthopedics': 2500,
    'pediatrics': 1500, 'dermatology': 2000, 'oncology': 4000,
}

# which doctor (created in user_management's 0014_seed_sri_lankan_people migration)
# sees patients in each appointment department
DOCTOR_USERNAME_BY_DEPARTMENT = {
    'cardiology': 'dr_priyantha', 'neurology': 'dr_ishara', 'orthopedics': 'dr_chaminda',
    'pediatrics': 'dr_sanduni', 'dermatology': 'dr_nadeeka', 'oncology': 'dr_ranjith',
    'general': 'dr_harsha',
}


def calculate_age(dob, on_date):
    # standard "has the birthday happened yet this year" age calculation
    return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))


def make_nic(dob, gender):
    # old style Sri Lankan NIC: 2 digit birth year + 3 digit day-of-year (women get +500) + 3 digit serial + V
    year_part = dob.strftime('%y')
    day_of_year = dob.timetuple().tm_yday
    if gender == 'female':
        day_of_year += 500
    serial = random.randint(100, 999)
    return f'{year_part}{day_of_year:03d}{serial}V'


def seed_appointments(apps, schema_editor):
    # historical (frozen) versions of the models, matching this migration's point in time
    User = apps.get_model('auth', 'User')
    Appointment = apps.get_model('appointment', 'Appointment')
    DepartmentFee = apps.get_model('appointment', 'DepartmentFee')
    Payment = apps.get_model('appointment', 'Payment')
    PrescriptionItem = apps.get_model('appointment', 'PrescriptionItem')
    PharmacyOrder = apps.get_model('appointment', 'PharmacyOrder')
    Medicine = apps.get_model('inventory', 'Medicine')

    today = date.today()  # today's date, used for every appointment date calculation below

    # give each department a realistic looking consultation fee
    for department_code, fee in DEPARTMENT_FEES.items():
        DepartmentFee.objects.filter(department=department_code).update(fee=fee)

    medicines = list(Medicine.objects.all())
    if not medicines:
        return  # the pharmacy catalog has not been seeded yet, nothing to prescribe

    # doctors, grouped by which appointment department they see patients for
    doctors_by_department = {code: [] for code in DOCTOR_USERNAME_BY_DEPARTMENT}
    for department_code, username in DOCTOR_USERNAME_BY_DEPARTMENT.items():
        doctor = User.objects.filter(username=username).first()
        if doctor:
            doctors_by_department[department_code].append(doctor)

    # the doctor the user made by hand before this migration also sees general patients
    original_doctor = User.objects.filter(profile__role='doctor').exclude(
        username__in=DOCTOR_USERNAME_BY_DEPARTMENT.values()
    ).first()
    if original_doctor:
        doctors_by_department['general'].append(original_doctor)

    department_codes = [code for code, doctors in doctors_by_department.items() if doctors]
    if not department_codes:
        return  # no doctors exist yet, nothing to book

    pharmacists = list(User.objects.filter(profile__role='pharmacist'))

    for patient in User.objects.filter(profile__role='patient'):
        # skip anyone who already has appointments, so this stays safe to run more than once
        if Appointment.objects.filter(patient=patient).exists():
            continue

        patient_dob = patient.profile.date_of_birth
        for _ in range(random.randint(1, 3)):  # each patient books 1 to 3 appointments
            department_code = random.choice(department_codes)
            doctor = random.choice(doctors_by_department[department_code])

            is_past = random.random() < 0.5  # half the appointments already happened
            if is_past:
                appointment_date = today - timedelta(days=random.randint(1, 60))
                status = random.choices(['confirmed', 'cancelled'], weights=[80, 20])[0]
            else:
                appointment_date = today + timedelta(days=random.randint(1, 30))
                status = random.choices(['pending', 'confirmed'], weights=[50, 50])[0]

            # historical User models don't carry the real get_full_name() method, so build it by hand
            patient_full_name = f'{patient.first_name} {patient.last_name}'.strip()

            appointment = Appointment.objects.create(
                patient=patient, department=department_code, doctor=doctor,
                date=appointment_date, time_slot=random.choice(TIME_SLOTS),
                message=random.choice(['', '', 'Follow up visit.', 'First time consultation.']),
                status=status, patient_name=patient_full_name,
                patient_contact=patient.profile.phone,
                patient_age=calculate_age(patient_dob, appointment_date) if patient_dob else 30,
                patient_address=patient.patient_profile.address,
                patient_nic=make_nic(patient_dob, patient.profile.gender) if patient_dob else '',
            )

            _create_payment(Payment, DepartmentFee, appointment, doctor, status)

            # only appointments that already happened and were confirmed get a completed consultation
            if is_past and status == 'confirmed' and pharmacists and random.random() < 0.6:
                _create_prescription_and_pharmacy_order(
                    PrescriptionItem, PharmacyOrder, appointment, medicines, pharmacists,
                )


def _create_payment(Payment, DepartmentFee, appointment, doctor, status):
    # look up this department's consultation fee
    department_fee_row = DepartmentFee.objects.filter(department=appointment.department).first()
    department_fee_amount = department_fee_row.fee if department_fee_row else 0
    # doctor's own fee, stored on their staff profile
    doctor_fee_amount = doctor.staff_profile.hourly_fee if hasattr(doctor, 'staff_profile') else 0
    total_amount = department_fee_amount + doctor_fee_amount

    if status == 'cancelled':
        # cancelled appointments were never paid for
        Payment.objects.create(
            appointment=appointment, amount=total_amount, doctor_fee_amount=doctor_fee_amount,
            method='cash', status='pending',
        )
    elif status == 'confirmed':
        # confirmed appointments are always paid, either online or by cash at reception
        method = random.choice(['online', 'cash'])
        ref_prefix = 'PAY' if method == 'online' else 'CASH'
        Payment.objects.create(
            appointment=appointment, amount=total_amount, doctor_fee_amount=doctor_fee_amount,
            method=method, status='paid', paid_at=timezone.now(),
            transaction_ref=f'{ref_prefix}-{appointment.pk:06d}',
        )
    else:  # pending
        # pending appointments chose to pay cash at the hospital, and have not paid yet
        Payment.objects.create(
            appointment=appointment, amount=total_amount, doctor_fee_amount=doctor_fee_amount,
            method='cash', status='pending',
        )


def _create_prescription_and_pharmacy_order(PrescriptionItem, PharmacyOrder, appointment, medicines, pharmacists):
    # the doctor prescribes 1 to 3 medicines for this appointment
    prescribed_medicines = random.sample(medicines, min(len(medicines), random.randint(1, 3)))
    total_amount = 0
    for medicine in prescribed_medicines:
        quantity = random.randint(1, 2) * 5  # e.g. 5, 10, 15, 20 units
        PrescriptionItem.objects.create(
            appointment=appointment, medicine=medicine,
            dosage=random.choice(['1 tablet', '2 tablets', '1 capsule', '10 ml']),
            quantity=quantity,
            instructions=random.choice([
                'Twice daily after meals for 5 days', 'Once daily in the morning',
                'Three times a day for 7 days', 'As needed for pain',
            ]),
        )
        total_amount += medicine.price * quantity

    # pick how far along the pharmacy counter workflow this order has gotten
    order_status = random.choices(['pending', 'dispensed', 'completed'], weights=[15, 25, 60])[0]
    payment_method = random.choice(['online', 'cash'])

    if order_status == 'pending':
        PharmacyOrder.objects.create(appointment=appointment, status='pending', total_amount=total_amount)
    elif order_status == 'dispensed':
        PharmacyOrder.objects.create(
            appointment=appointment, status='dispensed', total_amount=total_amount,
            dispensed_by=random.choice(pharmacists), dispensed_at=timezone.now(),
            payment_method=payment_method, payment_status='pending',
        )
    else:  # completed
        ref_prefix = 'PAY' if payment_method == 'online' else 'CASH'
        PharmacyOrder.objects.create(
            appointment=appointment, status='completed', total_amount=total_amount,
            dispensed_by=random.choice(pharmacists), dispensed_at=timezone.now(),
            payment_method=payment_method, payment_status='paid',
            transaction_ref=f'{ref_prefix}-{appointment.pk:06d}',
            paid_at=timezone.now(), completed_at=timezone.now(),
        )


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0007_seed_department_fees'),
        ('user_management', '0014_seed_sri_lankan_people'),
        ('inventory', '0004_seed_pharmacy_catalog'),
    ]

    operations = [
        migrations.RunPython(seed_appointments, reverse_noop),
    ]
