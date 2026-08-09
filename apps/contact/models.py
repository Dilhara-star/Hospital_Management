# models for supplier and medicine inventory management
from django.db import models  # import django's model tools
from datetime import date, timedelta  # import date tools to check expiry


# a supplier is a company that sells medicine to the hospital
class Contact_us(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('solved', 'Solved'),
        ]
    name = models.CharField(max_length=150)  # supplier company name
    email = models.EmailField(blank=True)  # email address of the supplier
    subject = models.CharField(blank=True)  # postal address of the supplier
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')  # active or inactive
    created_date = models.DateField(auto_now_add=True)  # date this supplier was added
    message = models.TextField(blank=True)  # any additional notes about the supplier


    # show the supplier name when printed
    def __str__(self):
        return self.name


