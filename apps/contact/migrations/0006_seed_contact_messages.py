from django.db import migrations  # base tools for writing a migration

# messages to create: (sender name, subject, status, message text)
MESSAGE_PLAN = [
    ('Nirmala Wijeratne', 'Question about visiting hours', 'pending',
     'Could you tell me the visiting hours for the cardiology ward? My father is admitted there.'),
    ('Saman Kodikara', 'Billing query', 'solved',
     'I was charged twice for my last appointment. Can someone please check my payment history?'),
    ('Fathima Rizvi', 'Appointment rescheduling', 'pending',
     'I need to move my appointment with Dr. Gunawardena to next week. Please advise how to do this.'),
    ('Gayan Abeywickrama', 'Feedback about service', 'solved',
     'The reception staff were very helpful during my last visit. Thank you very much.'),
    ('Thivya Rajaratnam', 'Pharmacy stock question', 'pending',
     'Does the hospital pharmacy currently stock Insulin Mixtard? I need to collect a refill this week.'),
    ('Ranil Amerasekera', 'General enquiry', 'solved',
     'Do you accept Ceylinco Life insurance for outpatient consultations?'),
]


def seed_contact_messages(apps, schema_editor):
    # historical (frozen) version of the model, matching this migration's point in time
    Contact_us = apps.get_model('contact', 'Contact_us')

    # stop here if this migration has already run before
    if Contact_us.objects.exists():
        return

    for name, subject, status, message in MESSAGE_PLAN:
        email = f'{name.split()[0].lower()}@example.lk'  # simple demo email address
        Contact_us.objects.create(name=name, email=email, subject=subject, status=status, message=message)


def reverse_noop(apps, schema_editor):
    pass  # nothing to undo, this migration only fills in missing demo data


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0005_merge_20260812_2315'),
    ]

    operations = [
        migrations.RunPython(seed_contact_messages, reverse_noop),
    ]
