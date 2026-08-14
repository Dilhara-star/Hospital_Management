import random  # used to pick random names, dates, numbers etc
from datetime import date, timedelta  # date math for birthdays and hire dates

from django.db import migrations  # base tools for writing a migration

# every demo account this migration creates shares this password
DEMO_PASSWORD = 'Passw0rd@123'

# three name groups (Sinhala, Tamil, Muslim) so a first name and surname picked
# together always sound like they belong to the same person
NAME_GROUPS = [
    {
        'male_first': ['Kasun', 'Nuwan', 'Chamara', 'Dinesh', 'Sampath', 'Ruwan', 'Tharindu',
                       'Lahiru', 'Chathura', 'Roshan', 'Suresh', 'Prasad', 'Nimal', 'Sunil',
                       'Ajith', 'Kumara', 'Harsha', 'Priyantha', 'Chaminda', 'Ranjith'],
        'female_first': ['Nimali', 'Chathuri', 'Dilani', 'Sanduni', 'Kavindya', 'Iresha',
                          'Tharushi', 'Anushka', 'Malki', 'Hansika', 'Kalani', 'Menaka',
                          'Nayana', 'Sithara', 'Dinusha', 'Ishara', 'Nadeeka'],
        'last': ['Perera', 'Fernando', 'Silva', 'Jayasuriya', 'Wickramasinghe', 'Gunawardena',
                 'Rajapaksa', 'Bandara', 'Dissanayake', 'Weerasinghe', 'Kariyawasam', 'Mendis',
                 'Rathnayake', 'Senanayake', 'Abeysekara', 'Herath', 'Wijesinghe',
                 'Karunaratne', 'Jayawardena', 'Amarasinghe'],
    },
    {
        'male_first': ['Kumar', 'Rajan', 'Vijay', 'Selvam', 'Mohan', 'Sivakumar', 'Prasath',
                       'Thevan', 'Gowri', 'Arun'],
        'female_first': ['Priya', 'Kalpana', 'Vani', 'Meena', 'Divya', 'Kavya', 'Nila',
                          'Shalini', 'Deepa', 'Ranjani'],
        'last': ['Murugan', 'Sivakumar', 'Thevarajah', 'Rajendran', 'Kandiah', 'Nadarajah',
                 'Sabaratnam', 'Kanagasabai', 'Pillai', 'Ratnam'],
    },
    {
        'male_first': ['Mohamed', 'Farhan', 'Rizwan', 'Nazeer', 'Imran', 'Shakir', 'Anwar',
                       'Fazal', 'Nizam', 'Hassan'],
        'female_first': ['Fathima', 'Ayesha', 'Nusra', 'Rifka', 'Shazna', 'Rukshana',
                          'Farzana', 'Nadira', 'Suhana', 'Rizana'],
        'last': ['Careem', 'Hameed', 'Rasheed', 'Marikar', 'Jabbar', 'Thassim', 'Lebbe',
                 'Rauff', 'Naina', 'Aboobucker'],
    },
]

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']  # blood type choices, minus the blank option
INSURERS = [  # insurance companies that really operate in Sri Lanka
    'Ceylinco Life Insurance', 'AIA Insurance Lanka', 'Sri Lanka Insurance Corporation',
    'Union Assurance', 'Softlogic Life Insurance',
]
ALLERGIES = ['Penicillin', 'Sulfa drugs', 'Peanuts', 'Dust', 'Seafood', 'None known']  # common allergy notes
CHRONIC_CONDITIONS = ['Diabetes Mellitus Type 2', 'Hypertension', 'Asthma', 'High Cholesterol']  # common condition notes
CITIES = [  # Sri Lankan cities used to build home addresses
    'Colombo', 'Kandy', 'Galle', 'Jaffna', 'Negombo', 'Kurunegala', 'Anuradhapura',
    'Matara', 'Ratnapura', 'Batticaloa', 'Nuwara Eliya', 'Gampaha', 'Kalutara',
    'Badulla', 'Trincomalee', 'Ampara', 'Polonnaruwa', 'Puttalam',
]
STREETS = [  # street name fragments used to build home addresses
    'Temple Road', 'Galle Road', 'Kandy Road', 'Lake Road', 'Station Road',
    'Main Street', 'Hill Street', 'Church Road', 'Park Avenue', 'Negombo Road',
    'High Level Road', 'Peradeniya Road',
]

# doctors to create: (first name, last name, gender, staff department, specialization)
DOCTOR_PLAN = [
    ('Priyantha', 'Wickramasinghe', 'male', 'cardiology', 'Consultant Cardiologist'),
    ('Ishara', 'Gunawardena', 'female', 'neurology', 'Consultant Neurologist'),
    ('Chaminda', 'Rathnayake', 'male', 'orthopedics', 'Consultant Orthopaedic Surgeon'),
    ('Sanduni', 'Abeysekara', 'female', 'pediatrics', 'Consultant Paediatrician'),
    ('Nadeeka', 'Karunaratne', 'female', 'other', 'Consultant Dermatologist'),
    ('Ranjith', 'Senanayake', 'male', 'other', 'Consultant Oncologist'),
    ('Harsha', 'Bandara', 'male', 'opd', 'General Physician'),
]

# support staff to create: (first name, last name, gender, role, staff department, qualification)
SUPPORT_STAFF_PLAN = [
    ('Kalani', 'Fernando', 'female', 'nurse', 'icu', 'BSc in Nursing (Hons)'),
    ('Ruwan', 'Dissanayake', 'male', 'nurse', 'emergency', 'Diploma in Nursing'),
    ('Menaka', 'Silva', 'female', 'nurse', 'opd', 'Diploma in Nursing'),
    ('Ishan', 'Perera', 'male', 'nurse', 'pediatrics', 'BSc in Nursing (Hons)'),
    ('Sithara', 'Jayawardena', 'female', 'receptionist', 'administration', 'Diploma in Office Management'),
    ('Dinusha', 'Mendis', 'female', 'receptionist', 'opd', 'Diploma in Office Management'),
    ('Kasun', 'Herath', 'male', 'receptionist', 'administration', 'Diploma in Office Management'),
    ('Nayana', 'Wijesinghe', 'female', 'pharmacist', 'pharmacy', 'BPharm (Hons)'),
    ('Roshan', 'Amarasinghe', 'male', 'pharmacist', 'pharmacy', 'BPharm (Hons)'),
    ('Chathura', 'Weerasinghe', 'male', 'lab_technician', 'laboratory', 'Diploma in Medical Laboratory Technology'),
    ('Iresha', 'Kariyawasam', 'female', 'lab_technician', 'laboratory', 'Diploma in Medical Laboratory Technology'),
]


def random_person():
    # pick one of the three name groups, then a gender, then matching names from that group
    group = random.choice(NAME_GROUPS)
    gender = random.choice(['male', 'female'])
    first_names = group['male_first'] if gender == 'male' else group['female_first']
    first_name = random.choice(first_names)
    last_name = random.choice(group['last'])
    return first_name, last_name, gender


def random_dob(min_age, max_age, today):
    # pick a random age inside the range, then a random day of that birth year
    age = random.randint(min_age, max_age)
    day_offset = random.randint(0, 364)
    birth_year = today.year - age
    try:
        return date(birth_year, 1, 1) + timedelta(days=day_offset)
    except ValueError:
        return date(birth_year, 1, 1)  # falls back to 1 Jan if the day does not exist


def make_phone():
    # Sri Lankan mobile numbers start with one of these network prefixes
    prefix = random.choice(['070', '071', '072', '074', '075', '076', '077', '078'])
    rest = random.randint(1000000, 9999999)
    return f'{prefix}{rest}'


def make_address():
    # e.g. "No. 45, Temple Road, Kandy"
    house_number = random.randint(1, 250)
    street = random.choice(STREETS)
    city = random.choice(CITIES)
    return f'No. {house_number}, {street}, {city}'


def seed_people(apps, schema_editor):
    # historical (frozen) versions of the models, matching this migration's point in time
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('user_management', 'UserProfile')
    PatientProfile = apps.get_model('user_management', 'PatientProfile')
    StaffProfile = apps.get_model('user_management', 'StaffProfile')

    # stop here if this migration has already added its demo admin account before
    if User.objects.filter(username='admin').exists():
        return

    today = date.today()  # today's date, used for every birthday/hire-date calculation below

    def make_user(first_name, last_name, role, gender, dob, phone, username_hint):
        # build a unique username from the hint, adding a number if it is already taken
        username = username_hint
        counter = 1
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f'{username_hint}{counter}'
        email = f'{username}@example.lk'  # simple demo email address
        user = User.objects.create_user(  # create the login account with a hashed password
            username=username, email=email, password=DEMO_PASSWORD,
            first_name=first_name, last_name=last_name,
        )
        UserProfile.objects.create(  # create the matching profile row
            user=user, role=role, gender=gender, date_of_birth=dob, phone=phone,
        )
        return user

    # ---- top up the two accounts the user already made by hand after the reset ----
    patient_profile = PatientProfile.objects.select_related('user').first()
    if patient_profile and not patient_profile.address:
        patient_profile.blood_type = random.choice(BLOOD_TYPES)
        patient_profile.address = make_address()
        patient_profile.allergies = 'None known'
        patient_profile.emergency_contact_name = 'Kamal Jayarathne'
        patient_profile.emergency_contact_phone = make_phone()
        patient_profile.emergency_contact_relationship = 'parent'
        patient_profile.save()

    staff_profile = StaffProfile.objects.select_related('user').first()
    if staff_profile and not staff_profile.department:
        staff_profile.department = 'opd'
        staff_profile.room_number = 'OPD 1'
        staff_profile.specialization = 'General Medicine'
        staff_profile.qualification = 'MBBS (Colombo), MD (General Medicine)'
        staff_profile.license_number = 'SLMC 18342'
        staff_profile.hire_date = today - timedelta(days=365 * 4)
        staff_profile.employment_type = 'full_time'
        staff_profile.shift = 'morning'
        staff_profile.hourly_fee = 1500
        staff_profile.emergency_contact_name = 'Samanthi Jaya'
        staff_profile.emergency_contact_phone = make_phone()
        staff_profile.save()
        if not staff_profile.employee_id:
            # StaffProfile.save() normally builds this automatically, but that custom save()
            # logic does not run on the historical model used inside a migration, so build it here
            staff_profile.employee_id = f'EMP-{staff_profile.pk:04d}'
            staff_profile.save(update_fields=['employee_id'])

    # ---- admin login, so the user can open /admin and see every table ----
    admin_user = User.objects.create_superuser(
        username='admin', email='admin@example.lk', password=DEMO_PASSWORD,
        first_name='Malindu', last_name='Peiris',
    )
    UserProfile.objects.create(
        user=admin_user, role='admin', gender='male',
        date_of_birth=random_dob(35, 45, today), phone=make_phone(),
    )
    admin_staff = StaffProfile.objects.create(
        user=admin_user, department='administration', specialization='Hospital Administration',
        qualification='MBA (Health Management)', hire_date=today - timedelta(days=365 * 6),
        employment_type='full_time', shift='morning',
    )
    admin_staff.employee_id = f'EMP-{admin_staff.pk:04d}'
    admin_staff.save(update_fields=['employee_id'])

    # ---- doctors, one per appointment department plus a second general doctor ----
    room_counter = 2  # the existing doctor already uses "OPD 1", so new doctors start from room 2
    for first_name, last_name, gender, staff_department, specialization in DOCTOR_PLAN:
        dob = random_dob(34, 60, today)  # doctors are 34 to 60 years old
        user = make_user(first_name, last_name, 'doctor', gender, dob, make_phone(), f'dr_{first_name.lower()}')
        staff = StaffProfile.objects.create(
            user=user, department=staff_department, room_number=f'Room {room_counter}',
            specialization=specialization, qualification='MBBS (Colombo), MD, MRCP',
            license_number=f'SLMC {random.randint(10000, 39999)}',
            hire_date=today - timedelta(days=random.randint(365, 365 * 15)),
            employment_type='full_time', shift=random.choice(['morning', 'afternoon', 'rotating']),
            hourly_fee=random.choice([1000, 1500, 2000, 2500, 3000]),
            emergency_contact_name=f'{random.choice(["Nimal", "Sunethra", "Kamal"])} {last_name}',
            emergency_contact_phone=make_phone(),
        )
        staff.employee_id = f'EMP-{staff.pk:04d}'
        staff.save(update_fields=['employee_id'])
        room_counter += 1

    # ---- nurses, receptionists, pharmacists, lab technicians ----
    for first_name, last_name, gender, role, staff_department, qualification in SUPPORT_STAFF_PLAN:
        dob = random_dob(22, 55, today)  # support staff are 22 to 55 years old
        user = make_user(first_name, last_name, role, gender, dob, make_phone(), f'{role}_{first_name.lower()}')
        staff = StaffProfile.objects.create(
            user=user, department=staff_department, qualification=qualification,
            license_number=f'REG-{random.randint(1000, 9999)}',
            hire_date=today - timedelta(days=random.randint(180, 365 * 10)),
            employment_type=random.choice(['full_time', 'full_time', 'part_time']),
            shift=random.choice(['morning', 'afternoon', 'night', 'rotating']),
            emergency_contact_name=f'{random.choice(["Nimal", "Sunethra", "Kamal", "Anoma"])} {last_name}',
            emergency_contact_phone=make_phone(),
        )
        staff.employee_id = f'EMP-{staff.pk:04d}'
        staff.save(update_fields=['employee_id'])

    # ---- patients ----
    for _ in range(14):  # 14 brand new patients, on top of the existing hand made account
        first_name, last_name, gender = random_person()
        dob = random_dob(5, 82, today)  # patients range from young children to elderly
        user = make_user(
            first_name, last_name, 'patient', gender, dob, make_phone(),
            f'{first_name.lower()}.{last_name.lower()}',
        )

        has_insurance = random.random() < 0.6  # 60% chance of having insurance
        insurance_provider = random.choice(INSURERS) if has_insurance else ''
        insurance_number = f'INS-{random.randint(100000, 999999)}' if has_insurance else ''
        insurance_expiry = today + timedelta(days=random.randint(30, 700)) if has_insurance else None

        patient = PatientProfile.objects.create(
            user=user, blood_type=random.choice(BLOOD_TYPES),
            allergies=random.choice(ALLERGIES + ['']),  # sometimes leave it blank
            chronic_conditions=random.choice(CHRONIC_CONDITIONS + ['', '', '']),  # mostly blank
            address=make_address(),
            emergency_contact_name=f'{random.choice(["Nimal", "Sunethra", "Kamal", "Anoma", "Priya"])} {last_name}',
            emergency_contact_phone=make_phone(),
            emergency_contact_relationship=random.choice(['spouse', 'parent', 'sibling', 'child', 'friend']),
            insurance_provider=insurance_provider, insurance_number=insurance_number,
            insurance_expiry=insurance_expiry, status='active',
        )
        # PatientProfile.save() normally builds the MRN automatically, but that custom save()
        # logic does not run on the historical model used inside a migration, so build it here
        patient.mrn = f'MRN-{patient.pk:05d}'
        patient.save(update_fields=['mrn'])


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0013_alter_patientprofile_id_alter_staffprofile_id_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(seed_people, reverse_noop),
    ]
