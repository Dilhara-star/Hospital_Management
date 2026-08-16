# models for supplier management
from django.db import models  # import django's model tools


# a supplier is a company that sells medicine to the hospital
class Supplier(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),  # supplier is currently supplying medicine
        ('inactive', 'Inactive'),  # supplier is not used right now
    ]

    name = models.CharField(max_length=150)  # supplier company name
    contact_person = models.CharField(max_length=100, blank=True)  # main contact person at the supplier
    phone = models.CharField(max_length=20, blank=True)  # phone number to reach the supplier
    email = models.EmailField(blank=True)  # email address of the supplier
    address = models.TextField(blank=True)  # postal address of the supplier
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')  # active or inactive
    created_date = models.DateField(auto_now_add=True)  # date this supplier was added

    class Meta:
        db_table = 'suppliers'  # name of this model's table in the database

    # show the supplier name when printed
    def __str__(self):
        return self.name
