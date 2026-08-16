import random  # used to pick a random landline number for each supplier

from django.db import migrations  # base tools for writing a migration

# suppliers to create: (company name, contact person, address)
SUPPLIER_PLAN = [
    ('State Pharmaceuticals Corporation', 'Nalin Jayasekara', 'No. 75, Sir Baron Jayathilake Mawatha, Colombo'),
    ('Hemas Pharmaceuticals (Pvt) Ltd', 'Chamila Rodrigo', 'No. 75, Braybrooke Place, Colombo'),
    ('George Steuart Health (Pvt) Ltd', 'Ashan Wickrama', 'No. 45, Sir Baron Jayathilake Mawatha, Colombo'),
    ('Interpharm Ceylon (Pvt) Ltd', 'Manisha Peiris', 'No. 21, Kandy Road, Kelaniya'),
    ('Deshapriya Distributors', 'Sarath Kumara', 'No. 12, Peradeniya Road, Kandy'),
]


def seed_suppliers(apps, schema_editor):
    # historical (frozen) version of the model, matching this migration's point in time
    Supplier = apps.get_model('supplier', 'Supplier')

    # stop here if this migration has already run before
    if Supplier.objects.exists():
        return

    for name, contact_person, address in SUPPLIER_PLAN:
        # turn the company name into a short lowercase slug, for a fake email address
        slug = name.lower().replace(' ', '').replace('(', '').replace(')', '')[:20]
        Supplier.objects.create(
            name=name, contact_person=contact_person,
            phone=f'011{random.randint(2000000, 2999999)}',  # Colombo area landline style
            email=f'info@{slug}.lk', address=address, status='active',
        )


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_suppliers, reverse_noop),
    ]
