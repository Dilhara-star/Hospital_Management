from django.db import migrations


def seed_doctor_hourly_fees(apps, schema_editor):
    # give every doctor a demo hourly fee, so reports have real numbers to show
    UserProfile = apps.get_model('user_management', 'UserProfile')
    StaffProfile = apps.get_model('user_management', 'StaffProfile')

    demo_fees = [1000, 1500, 2000, 2500]  # cycles through these values, one per doctor
    doctors = UserProfile.objects.filter(role='doctor').order_by('id')

    for index, profile in enumerate(doctors):
        staff_profile, _created = StaffProfile.objects.get_or_create(user_profile=profile)
        if staff_profile.hourly_fee == 0:  # do not overwrite a fee someone already set
            staff_profile.hourly_fee = demo_fees[index % len(demo_fees)]
            staff_profile.save()


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0005_staffprofile_hourly_fee'),
    ]

    operations = [
        migrations.RunPython(seed_doctor_hourly_fees, reverse_noop),
    ]
