# step 1 of 3: add the new "user" column on StaffProfile.
# it starts empty (null=True) because existing rows do not have a value yet.
# the next migration will fill it in, then a third migration will lock it down.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0008_alter_patientprofile_id_alter_staffprofile_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='staffprofile',
            name='user',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='staff_profile_new',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
