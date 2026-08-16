from django.conf import settings
from django.db import models


class PrescriptionItem(models.Model):
    # one row is one medicine the doctor prescribed during an appointment
    appointment = models.ForeignKey(
        'appointment.Appointment',
        on_delete=models.CASCADE,
        related_name='prescription_items',
    )  # which appointment this medicine was prescribed on
    medicine = models.ForeignKey(
        'stock.Medicine',
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

    # text shown for this row in the admin site and in debug output
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
    appointment = models.OneToOneField('appointment.Appointment', on_delete=models.CASCADE, related_name='pharmacy_order')
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

    # text shown for this row in the admin site and in debug output
    def __str__(self):
        return f"Pharmacy order for {self.appointment} - {self.status}"
