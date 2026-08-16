import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('appointment', '0003_departmentfee_payment'),
        ('stock', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrescriptionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosage', models.CharField(max_length=100)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('instructions', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescription_items', to='appointment.appointment')),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescription_items', to='stock.medicine')),
            ],
            options={
                'verbose_name': 'Prescription Item',
                'verbose_name_plural': 'Prescription Items',
                'db_table': 'prescription_items',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='PharmacyOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Waiting for Pharmacist'), ('dispensed', 'Medicine Given - Awaiting Payment'), ('completed', 'Completed')], default='pending', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('payment_method', models.CharField(blank=True, choices=[('online', 'Online'), ('cash', 'Cash to Pharmacist')], max_length=10)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid')], default='pending', max_length=10)),
                ('transaction_ref', models.CharField(blank=True, max_length=50)),
                ('dispensed_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('appointment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pharmacy_order', to='appointment.appointment')),
                ('dispensed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dispensed_orders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pharmacy Order',
                'verbose_name_plural': 'Pharmacy Orders',
                'db_table': 'pharmacy_orders',
            },
        ),
    ]
