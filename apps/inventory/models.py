# models for supplier and medicine inventory management
from django.db import models  # import django's model tools
from datetime import date, timedelta  # import date tools to check expiry


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

    # show the supplier name when printed
    def __str__(self):
        return self.name


# medicine is the catalog entry for one type of medicine, like "Paracetamol 500mg"
class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('', '---------'),  # empty choice shown first
        ('tablet', 'Tablet'),  # solid pill form
        ('capsule', 'Capsule'),  # capsule form
        ('syrup', 'Syrup'),  # liquid form
        ('injection', 'Injection'),  # injectable form
        ('ointment', 'Ointment'),  # cream/ointment form
        ('drops', 'Drops'),  # eye/ear drops form
        ('other', 'Other'),  # anything else
    ]
    UNIT_CHOICES = [
        ('', '---------'),  # empty choice shown first
        ('tablet', 'Tablet'),  # counted in tablets
        ('bottle', 'Bottle'),  # counted in bottles
        ('strip', 'Strip'),  # counted in strips
        ('box', 'Box'),  # counted in boxes
        ('vial', 'Vial'),  # counted in vials
    ]

    name = models.CharField(max_length=150)  # name of the medicine
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True)  # what form the medicine is
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, blank=True)  # how the medicine is counted
    manufacturer = models.CharField(max_length=150, blank=True)  # company that makes the medicine
    reorder_level = models.PositiveIntegerField(default=10)  # minimum quantity before we need to reorder
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # price charged to the patient per unit
    description = models.TextField(blank=True)  # extra notes about the medicine

    # add up the quantity of every stock batch for this medicine
    @property
    def total_quantity(self):
        result = self.stock_batches.aggregate(total=models.Sum('quantity'))  # sum the quantity field
        return result['total'] or 0  # return 0 if there are no batches yet

    # true if the total stock is at or below the reorder level
    @property
    def is_low_stock(self):
        return self.total_quantity <= self.reorder_level

    # show the medicine name when printed
    def __str__(self):
        return self.name


# a stock batch is one delivery of medicine, with its own quantity and expiry date
class MedicineStock(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_batches')  # which medicine this batch is for
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_batches')  # which supplier delivered this batch
    batch_number = models.CharField(max_length=50)  # batch code printed on the packaging
    quantity = models.PositiveIntegerField(default=0)  # how many units are left in this batch
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # price paid for this batch
    expiry_date = models.DateField()  # date this batch expires
    received_date = models.DateField(auto_now_add=True)  # date this batch was added to stock

    # true if the expiry date has already passed
    @property
    def is_expired(self):
        return self.expiry_date < date.today()

    # true if the batch will expire within the next 30 days
    @property
    def is_expiring_soon(self):
        today = date.today()  # get today's date
        return today <= self.expiry_date <= today + timedelta(days=30)  # check if expiry is within 30 days

    class Meta:
        ordering = ['expiry_date']  # show batches that expire soonest first

    # show the medicine name and batch number when printed
    def __str__(self):
        return f"{self.medicine.name} - Batch {self.batch_number}"
