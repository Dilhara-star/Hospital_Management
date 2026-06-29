from django.db import models
from django.contrib.auth.models import User
from datetime import date


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
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

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class PatientProfile(models.Model):
    BLOOD_TYPE_CHOICES = [
        ('', '---------'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discharged', 'Discharged'),
    ]
    RELATIONSHIP_CHOICES = [
        ('', '---------'),
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('child', 'Child'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    mrn = models.CharField(max_length=20, unique=True, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    registered_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new and not self.mrn:
            self.mrn = f'MRN-{self.pk:05d}'
            PatientProfile.objects.filter(pk=self.pk).update(mrn=self.mrn)

    @property
    def age(self):
        try:
            dob = self.user.profile.date_of_birth
            if dob:
                today = date.today()
                return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            pass
        return None

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.mrn})"


class StaffProfile(models.Model):
    DEPARTMENT_CHOICES = [
        ('', '---------'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
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
    EMPLOYMENT_TYPE_CHOICES = [
        ('', '---------'),
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]
    SHIFT_CHOICES = [
        ('', '---------'),
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('night', 'Night'),
        ('rotating', 'Rotating'),
    ]

    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=30, choices=DEPARTMENT_CHOICES, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new and not self.employee_id:
            self.employee_id = f'EMP-{self.pk:04d}'
            StaffProfile.objects.filter(pk=self.pk).update(employee_id=self.employee_id)

    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} ({self.employee_id})"
