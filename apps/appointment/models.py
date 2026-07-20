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
    # list of fixed one hour time slots, from 9 AM to 5 PM
    TIME_SLOT_CHOICES = [
        ('', 'Select Time Slot'),
        ('09:00-10:00', '09:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 01:00 PM'),
        ('13:00-14:00', '01:00 PM - 02:00 PM'),
        ('14:00-15:00', '02:00 PM - 03:00 PM'),
        ('15:00-16:00', '03:00 PM - 04:00 PM'),
        ('16:00-17:00', '04:00 PM - 05:00 PM'),
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
    # time_slot stores the chosen one hour slot, like "09:00-10:00"
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # patient details filled in on the "patient details" step of the form
    patient_name = models.CharField(max_length=100)  # full name of the patient
    patient_contact = models.CharField(max_length=20)  # phone number of the patient
    patient_age = models.PositiveIntegerField()  # age of the patient in years
    patient_address = models.CharField(max_length=255)  # home address of the patient
    patient_nic = models.CharField(max_length=20)  # national identity card number

    class Meta:
        db_table = 'appointments'
        ordering = ['-created_at']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'

    def __str__(self):
        doctor_name = self.doctor.get_full_name() if self.doctor else 'Unassigned'
        return f"{self.patient.get_full_name()} - {doctor_name} ({self.date})"


class DepartmentFee(models.Model):
    # one row per department, holds how much a consultation costs there
    department = models.CharField(max_length=20, choices=Appointment.DEPARTMENT_CHOICES, unique=True)  # which department this price is for
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # the consultation price

    class Meta:
        db_table = 'department_fees'
        verbose_name = 'Department Fee'
        verbose_name_plural = 'Department Fees'

    def __str__(self):
        return f"{self.get_department_display()} - {self.fee}"  # e.g. "Cardiology - 50.00"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('online', 'Online'),  # patient paid with the demo online payment form
        ('cash', 'Cash at Hospital'),  # patient will pay in person at reception
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),  # money not received yet
        ('paid', 'Paid'),  # money received
    ]

    # each appointment has exactly one payment record
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # total fee charged: department fee + doctor fee
    doctor_fee_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # snapshot of just the doctor's own cut, for revenue reports
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)  # how the patient is paying
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # has it been paid yet
    transaction_ref = models.CharField(max_length=50, blank=True)  # fake receipt/reference number
    paid_at = models.DateTimeField(null=True, blank=True)  # when the payment was marked as paid
    created_at = models.DateTimeField(auto_now_add=True)  # when this payment record was created

    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment for {self.appointment} - {self.status}"


class PrescriptionItem(models.Model):
    # one row is one medicine the doctor prescribed during this appointment
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='prescription_items',
    )  # which appointment this medicine was prescribed on
    medicine = models.ForeignKey(
        'inventory.Medicine',
        on_delete=models.CASCADE,
        related_name='prescription_items',
    )  # which medicine from the pharmacy catalog was picked
    dosage = models.CharField(max_length=100)  # how much to take, e.g. "1 tablet"
    quantity = models.PositiveIntegerField(default=1)  # how many units to give the patient
    instructions = models.CharField(max_length=255, blank=True)  # e.g. "twice daily after meals, 5 days"
    created_at = models.DateTimeField(auto_now_add=True)  # when this medicine was added to the prescription

    class Meta:
        db_table = 'prescription_items'
        ordering = ['created_at']
        verbose_name = 'Prescription Item'
        verbose_name_plural = 'Prescription Items'

    def __str__(self):
        return f"{self.medicine.name} for {self.appointment}"


class PharmacyOrder(models.Model):
    # one row per appointment, tracks handing out the prescribed medicine and paying for it
    STATUS_CHOICES = [
        ('pending', 'Waiting for Pharmacist'),  # doctor prescribed medicine, pharmacist has not given it out yet
        ('dispensed', 'Medicine Given - Awaiting Payment'),  # pharmacist gave the medicine, waiting on payment
        ('completed', 'Completed'),  # medicine given and paid for, order is done
    ]
    METHOD_CHOICES = [
        ('online', 'Online'),  # patient paid with the demo online payment button
        ('cash', 'Cash to Pharmacist'),  # patient paid cash directly to the pharmacist
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),  # money not received yet
        ('paid', 'Paid'),  # money received
    ]

    # each appointment has exactly one pharmacy order
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='pharmacy_order')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # where the order is in the flow
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # total price of the prescribed medicine
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES, blank=True)  # how the patient paid
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')  # has it been paid yet
    transaction_ref = models.CharField(max_length=50, blank=True)  # fake receipt/reference number
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_orders',
    )  # which pharmacist handed out the medicine
    dispensed_at = models.DateTimeField(null=True, blank=True)  # when the medicine was handed out
    paid_at = models.DateTimeField(null=True, blank=True)  # when the payment was marked as paid
    completed_at = models.DateTimeField(null=True, blank=True)  # when the pharmacist marked the order complete
    created_at = models.DateTimeField(auto_now_add=True)  # when this order row was first created

    class Meta:
        db_table = 'pharmacy_orders'
        verbose_name = 'Pharmacy Order'
        verbose_name_plural = 'Pharmacy Orders'

    def __str__(self):
        return f"Pharmacy order for {self.appointment} - {self.status}"
