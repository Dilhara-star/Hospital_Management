# step 2 of 3: copy the user id across for every existing staff row.
# before: staff_profile.user_profile.user  (two hops through UserProfile)
# after:  staff_profile.user               (one hop, straight to the login account)

from django.db import migrations


def copy_user_onto_staff_profile(apps, schema_editor):
    # get the historical version of the model, matching this point in migration history
    StaffProfile = apps.get_model('user_management', 'StaffProfile')
    # go through every staff row that exists so far
    for staff_profile in StaffProfile.objects.all():
        # copy the user id from the old path (user_profile -> user) onto the new "user" field
        staff_profile.user_id = staff_profile.user_profile.user_id
        staff_profile.save(update_fields=['user'])


def reverse_copy(apps, schema_editor):
    pass  # nothing to undo, the old user_profile column still has the same data


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0009_staffprofile_user'),
    ]

    operations = [
        migrations.RunPython(copy_user_onto_staff_profile, reverse_copy),
    ]
