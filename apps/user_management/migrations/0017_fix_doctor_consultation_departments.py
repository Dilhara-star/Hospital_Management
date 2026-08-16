from django.db import migrations  # base tools for writing a migration

# doctors whose staff department was set to a placeholder ('other' or 'opd') during seeding,
# because the old department choices had no exact match for their real specialty.
# each row is: specialization text used at seed time, correct department code to set now.
FIXES = [
    ('Consultant Dermatologist', 'dermatology'),
    ('Consultant Oncologist', 'oncology'),
    ('General Physician', 'general'),
]


def fix_departments(apps, schema_editor):
    # historical (frozen) version of the model, matching this migration's point in time
    StaffProfile = apps.get_model('user_management', 'StaffProfile')

    for specialization, correct_department in FIXES:
        # only touch rows still on a placeholder value, so a manual admin edit is never overwritten
        StaffProfile.objects.filter(
            specialization=specialization,
            department__in=['other', 'opd'],
        ).update(department=correct_department)


def reverse_noop(apps, schema_editor):
    pass  # nothing worth undoing, this migration only corrects seeded placeholder values


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0016_alter_staffprofile_department_choices'),
    ]

    operations = [
        migrations.RunPython(fix_departments, reverse_noop),
    ]
