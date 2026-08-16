import random  # used to pick random suppliers, quantities, expiry dates
from datetime import date, timedelta  # date math for expiry dates

from django.db import migrations  # base tools for writing a migration

# companies that make the medicine, picked at random for each catalog entry
MANUFACTURERS = [
    'State Pharmaceuticals Manufacturing Corporation', 'Hemas Pharmaceuticals (Pvt) Ltd',
    'ACL Pharmaceuticals', "J.L. Morison Son & Jones (Ceylon) PLC",
    'Link Natural Products (Pvt) Ltd', 'Cipla Lanka (Pvt) Ltd',
]

# medicines to create: (name, category, unit, price, reorder level)
MEDICINE_PLAN = [
    ('Paracetamol 500mg', 'tablet', 'tablet', 2.00, 500),
    ('Amoxicillin 250mg', 'capsule', 'strip', 8.00, 300),
    ('Omeprazole 20mg', 'capsule', 'strip', 12.00, 200),
    ('Metformin 500mg', 'tablet', 'strip', 5.00, 300),
    ('Amlodipine 5mg', 'tablet', 'strip', 6.00, 200),
    ('Cetirizine 10mg', 'tablet', 'strip', 4.00, 200),
    ('Ibuprofen 400mg', 'tablet', 'strip', 3.00, 300),
    ('Salbutamol Inhaler', 'other', 'box', 450.00, 20),
    ('Vitamin C 500mg', 'tablet', 'strip', 3.50, 400),
    ('ORS Sachet', 'other', 'box', 25.00, 100),
    ('Ranitidine 150mg', 'tablet', 'strip', 5.00, 200),
    ('Aspirin 75mg', 'tablet', 'strip', 2.50, 300),
    ('Atorvastatin 10mg', 'tablet', 'strip', 15.00, 150),
    ('Ceftriaxone 1g Injection', 'injection', 'vial', 350.00, 50),
    ('Insulin Mixtard 30/70', 'injection', 'vial', 850.00, 30),
    ('Diclofenac Gel', 'ointment', 'box', 180.00, 40),
    ('Chlorpheniramine Syrup', 'syrup', 'bottle', 120.00, 60),
    ('Losartan 50mg', 'tablet', 'strip', 9.00, 200),
    ('Domperidone 10mg', 'tablet', 'strip', 6.00, 150),
    ('Ciprofloxacin Eye Drops', 'drops', 'bottle', 220.00, 30),
]


def seed_medicine_catalog(apps, schema_editor):
    # historical (frozen) versions of the models, matching this migration's point in time
    Supplier = apps.get_model('supplier', 'Supplier')
    Medicine = apps.get_model('stock', 'Medicine')
    MedicineStock = apps.get_model('stock', 'MedicineStock')

    # stop here if this migration has already run before
    if Medicine.objects.exists():
        return

    suppliers = list(Supplier.objects.all())
    if not suppliers:
        return  # suppliers have not been seeded yet, nothing to link a stock batch to

    today = date.today()  # today's date, used for every expiry date calculation below

    # ---- medicines, each with one starting stock batch ----
    for index, (name, category, unit, price, reorder_level) in enumerate(MEDICINE_PLAN):
        medicine = Medicine.objects.create(
            name=name, category=category, unit=unit,
            manufacturer=random.choice(MANUFACTURERS),
            reorder_level=reorder_level, price=price,
        )

        is_low_stock = index < 2  # the first two medicines are seeded low, to test "low stock" alerts
        is_expiring_soon = index == 2  # the third medicine expires soon, to test "expiring soon" alerts
        if is_low_stock:
            quantity = max(reorder_level - 20, 5)
            expiry_date = today + timedelta(days=random.randint(180, 700))
        elif is_expiring_soon:
            quantity = reorder_level * 3
            expiry_date = today + timedelta(days=random.randint(5, 25))
        else:
            quantity = reorder_level * random.randint(3, 8)
            expiry_date = today + timedelta(days=random.randint(180, 730))

        MedicineStock.objects.create(
            medicine=medicine,
            supplier=random.choice(suppliers),
            batch_number=f'B{today.year}{random.randint(1000, 9999)}',
            quantity=quantity,
            purchase_price=round(price * 0.6, 2),  # hospital buys it for less than it sells it
            expiry_date=expiry_date,
        )


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
        ('supplier', '0002_seed_suppliers'),
    ]

    operations = [
        migrations.RunPython(seed_medicine_catalog, reverse_noop),
    ]
