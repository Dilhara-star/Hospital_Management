from django.db import models  # django's model tools, used to build database tables
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from datetime import date  # used to work out someone's age from their date of birth


class UserProfile(models.Model):
    # drop-down choices for gender
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    # drop-down choices for role
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('user', 'User'),
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('pharmacist', 'Pharmacist'),
        ('lab_technician', 'Lab Technician'),
    ]

    # one profile belongs to exactly one User; deleting the User deletes this profile too
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # phone number, can be left blank
    phone = models.CharField(max_length=20, blank=True)
    # date of birth, can be left empty
    date_of_birth = models.DateField(null=True, blank=True)
    # gender, can be left blank
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    # role (patient, doctor, admin, etc), must always be set
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    # profile picture upload, can be left empty
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    class Meta:
        db_table = 'user_profiles'  # name of this model's table in the database

    # text shown for this row in the admin site and dropdowns
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class PatientProfile(models.Model):
    # drop-down choices for blood type
    BLOOD_TYPE_CHOICES = [
        ('', '---------'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    # drop-down choices for patient status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discharged', 'Discharged'),
    ]
    # drop-down choices for emergency contact relationship
    RELATIONSHIP_CHOICES = [
        ('', '---------'),
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]

    # one patient record belongs to exactly one User; deleting the User deletes this record too
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    # medical record number, auto-filled after saving, must be unique
    mrn = models.CharField(max_length=20, unique=True, blank=True)
    # blood type, can be left blank
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    # known allergies, can be left blank
    allergies = models.TextField(blank=True)
    # chronic conditions, can be left blank
    chronic_conditions = models.TextField(blank=True)
    # home address, can be left blank
    address = models.TextField(blank=True)
    # emergency contact name, can be left blank
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    # emergency contact phone, can be left blank
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    # emergency contact relationship, can be left blank
    emergency_contact_relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True)
    # insurance provider name, can be left blank
    insurance_provider = models.CharField(max_length=100, blank=True)
    # insurance policy number, can be left blank
    insurance_number = models.CharField(max_length=50, blank=True)
    # insurance expiry date, can be left empty
    insurance_expiry = models.DateField(null=True, blank=True)
    # date this patient was registered, filled in automatically the first time
    registered_date = models.DateField(auto_now_add=True)
    # patient status, defaults to active
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'patient_profiles'  # name of this model's table in the database

    # saves the patient, auto-building their MRN (medical record number) the first time
    def save(self, *args, **kwargs):
        # check if this is a brand new row (no id yet)
        is_new = not self.pk
        # save the row first, so Django gives it an id (self.pk)
        super().save(*args, **kwargs)
        # if it's new and has no MRN yet, build one from its own id
        if is_new and not self.mrn:
            self.mrn = f'MRN-{self.pk:05d}'
            # update just the mrn column, to avoid running save() again
            PatientProfile.objects.filter(pk=self.pk).update(mrn=self.mrn)

    # works out the patient's age from their date of birth
    @property
    def age(self):
        try:
            dob = self.user.profile.date_of_birth
            if dob:
                today = date.today()
                return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass
        # no date of birth on file, so we don't know their age
        return None

    # text shown for this row in the admin site and dropdowns
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.mrn})"


class StaffProfile(models.Model):
    # drop-down choices for department
    DEPARTMENT_CHOICES = [
        ('', '---------'),
        ('general', 'General Consultation'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('dermatology', 'Dermatology'),
        ('oncology', 'Oncology'),
        ('emergency', 'Emergency'),
        ('icu', 'ICU'),
        ('opd', 'OPD'),
        ('pharmacy', 'Pharmacy'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('surgery', 'Surgery'),
        ('administration', 'Administration'),
        ('other', 'Other'),
    ]
    # drop-down choices for employment type
    EMPLOYMENT_TYPE_CHOICES = [
        ('', '---------'),
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]
    # drop-down choices for shift
    SHIFT_CHOICES = [
        ('', '---------'),
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('night', 'Night'),
        ('rotating', 'Rotating'),
    ]

    # one staff record belongs to exactly one User; deleting the User deletes this record too
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    # employee id, auto-filled after saving, must be unique
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    # department, can be left blank
    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES, blank=True)
    # which room this staff member sees patients in, e.g. a doctor
    room_number = models.CharField(max_length=20, blank=True)
    # specialization, can be left blank
    specialization = models.CharField(max_length=100, blank=True)
    # qualification, can be left blank
    qualification = models.CharField(max_length=100, blank=True)
    # license number, can be left blank
    license_number = models.CharField(max_length=50, blank=True)
    # hire date, can be left empty
    hire_date = models.DateField(null=True, blank=True)
    # employment type, can be left blank
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    # shift, can be left blank
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, blank=True)
    # emergency contact name, can be left blank
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    # emergency contact phone, can be left blank
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    # doctor's own consultation fee, added on top of the department fee (only meaningful for doctors)
    hourly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    # how many years this doctor has practiced, shown on the "Find a Doctor" page (only meaningful for doctors)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True, default=0)

    class Meta:
        db_table = 'staff_profiles'  # name of this model's table in the database

    # saves the staff member, auto-building their employee id the first time
    def save(self, *args, **kwargs):
        # check if this is a brand new row (no id yet)
        is_new = not self.pk
        # save the row first, so Django gives it an id (self.pk)
        super().save(*args, **kwargs)
        # if it's new and has no employee id yet, build one from its own id
        if is_new and not self.employee_id:
            self.employee_id = f'EMP-{self.pk:04d}'
            # update just the employee_id column, to avoid running save() again
            StaffProfile.objects.filter(pk=self.pk).update(employee_id=self.employee_id)

    # text shown for this row in the admin site and dropdowns
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
