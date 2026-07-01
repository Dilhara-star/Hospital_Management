from django.conf import settings
from django.db import models


class Appointment(models.Model):
    DEPARTMENT_CHOICES = [
        ('', 'Select Department'),
        ('general', 'General Consultation'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('dermatology', 'Dermatology'),
        ('oncology', 'Oncology'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
    )
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'profile__role': 'doctor'},
        related_name='doctor_appointments',
    )
    date = models.DateField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        doctor_name = self.doctor.get_full_name() if self.doctor else 'Unassigned'
        return f"{self.patient.get_full_name()} - {doctor_name} ({self.date})"
