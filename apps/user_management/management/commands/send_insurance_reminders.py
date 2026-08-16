# management command: run this by hand, or schedule it daily (e.g. Windows Task
# Scheduler running "python manage.py send_insurance_reminders"), to email every
# patient whose insurance policy expires within the next 30 days.
from datetime import timedelta  # used to work out the 30 day reminder window
from django.core.management.base import BaseCommand  # base class every management command extends
from django.utils import timezone  # used to get today's date
from apps.user_management.models import PatientProfile  # the model holding insurance_expiry
from apps.user_management.notifications import send_insurance_expiry_email  # sends the reminder email


class Command(BaseCommand):
    help = 'Emails every patient whose insurance policy expires within the next 30 days.'

    # finds every patient with insurance expiring in the next 30 days and emails each one a reminder
    def handle(self, **options):
        today = timezone.now().date()  # today's date
        cutoff = today + timedelta(days=30)  # the last date we still count as "expiring soon"

        # patients with an insurance expiry date that falls between today and the cutoff
        patients = PatientProfile.objects.select_related('user').exclude(
            insurance_expiry__isnull=True,
        ).filter(insurance_expiry__range=(today, cutoff))

        for patient in patients:
            send_insurance_expiry_email(patient)  # email this one patient

        self.stdout.write(f'Sent {patients.count()} insurance expiry reminder email(s).')
