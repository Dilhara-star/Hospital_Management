from django.db import migrations  # base tools for writing a migration


def promote_to_admin(apps, schema_editor):
    # historical (frozen) versions of the models, matching this migration's point in time
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('user_management', 'UserProfile')
    PatientProfile = apps.get_model('user_management', 'PatientProfile')
    StaffProfile = apps.get_model('user_management', 'StaffProfile')

    # find the hand-made account by its email, do nothing if it is missing or already an admin
    user = User.objects.filter(email='roomikat@gmail.com').first()
    if user is None or user.profile.role == 'admin':
        return

    # switch the role to admin
    user.profile.role = 'admin'
    user.profile.save()

    # a person cannot be both a patient and staff at the same time, so drop the old patient record
    PatientProfile.objects.filter(user=user).delete()

    # make sure they have an employment record too, like every other staff member
    staff_profile, created = StaffProfile.objects.get_or_create(user=user)
    if created and not staff_profile.employee_id:
        # StaffProfile.save() normally builds this automatically, but that custom save()
        # logic does not run on the historical model used inside a migration, so build it here
        staff_profile.employee_id = f'EMP-{staff_profile.pk:04d}'
        staff_profile.save(update_fields=['employee_id'])


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only promotes one hand-made account


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0014_seed_sri_lankan_people'),
    ]

    operations = [
        migrations.RunPython(promote_to_admin, reverse_noop),
    ]
