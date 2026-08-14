# models for the "Contact Us" inquiry form
from django.db import models  # import django's model tools


# one row is one message sent through the public "Contact Us" form
class Contact_us(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('solved', 'Solved'),
        ]
    name = models.CharField(max_length=150)  # name of the person who sent the message
    email = models.EmailField(blank=True)  # email address to reply to
    subject = models.CharField(blank=True)  # subject line they typed
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # pending or solved
    created_date = models.DateField(auto_now_add=True)  # date this message was sent
    message = models.TextField(blank=True)  # the message itself

    class Meta:
        db_table = 'contact_messages'  # name of this model's table in the database

    # show the sender's name when printed
    def __str__(self):
        return self.name


