import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('supplier', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Medicine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('category', models.CharField(blank=True, choices=[('', '---------'), ('tablet', 'Tablet'), ('capsule', 'Capsule'), ('syrup', 'Syrup'), ('injection', 'Injection'), ('ointment', 'Ointment'), ('drops', 'Drops'), ('other', 'Other')], max_length=20)),
                ('unit', models.CharField(blank=True, choices=[('', '---------'), ('tablet', 'Tablet'), ('bottle', 'Bottle'), ('strip', 'Strip'), ('box', 'Box'), ('vial', 'Vial')], max_length=20)),
                ('manufacturer', models.CharField(blank=True, max_length=150)),
                ('reorder_level', models.PositiveIntegerField(default=10)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'medicines',
            },
        ),
        migrations.CreateModel(
            name='MedicineStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_number', models.CharField(max_length=50)),
                ('quantity', models.PositiveIntegerField(default=0)),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('expiry_date', models.DateField()),
                ('received_date', models.DateField(auto_now_add=True)),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_batches', to='stock.medicine')),
                ('supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stock_batches', to='supplier.supplier')),
            ],
            options={
                'db_table': 'medicine_stocks',
                'ordering': ['expiry_date'],
            },
        ),
    ]
