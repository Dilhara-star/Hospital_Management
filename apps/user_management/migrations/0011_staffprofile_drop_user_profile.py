# step 3 of 3: remove the old "user_profile" column, and lock the new
# "user" column in as required, with its final name "staff_profile"
# for looking it up from a User (e.g. some_user.staff_profile).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0010_migrate_staffprofile_user_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='staffprofile',
            name='user_profile',
        ),
        migrations.AlterField(
            model_name='staffprofile',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='staff_profile',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
