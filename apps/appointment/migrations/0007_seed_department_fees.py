from django.db import migrations


def seed_department_fees(apps, schema_editor):
    # give every department a demo consultation fee, so appointment costs are not zero
    DepartmentFee = apps.get_model('appointment', 'DepartmentFee')

    # department codes copied from Appointment.DEPARTMENT_CHOICES (skip the blank "Select Department" choice)
    department_codes = [
        'general', 'cardiology', 'neurology', 'orthopedics',
        'pediatrics', 'dermatology', 'oncology',
    ]

    for code in department_codes:
        fee_row, created = DepartmentFee.objects.get_or_create(department=code, defaults={'fee': 1500})
        if not created and fee_row.fee == 0:  # do not overwrite a fee staff already configured
            fee_row.fee = 1500
            fee_row.save()


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('appointment', '0006_payment_doctor_fee_amount'),
    ]

    operations = [
        migrations.RunPython(seed_department_fees, reverse_noop),
    ]
