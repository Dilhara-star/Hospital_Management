# management command: run this by hand, or schedule it daily (e.g. Windows Task
# Scheduler running "python manage.py send_expiry_alerts"), to email the admin
# a digest of any medicine stock batches that are expired or expiring soon.
from django.core.management.base import BaseCommand  # base class every management command extends
from apps.stock.models import MedicineStock  # the stock batch model we are checking
from apps.stock.notifications import send_expiry_alert_admin_email  # sends the digest email


class Command(BaseCommand):
    help = 'Emails the admin a digest of medicine stock batches that are expired or expiring within 30 days.'

    # finds every expired/expiring stock batch and emails the admin a digest
    def handle(self, **options):
        # only look at batches that still have stock left - an empty batch does not need a reorder alert
        batches = MedicineStock.objects.select_related('medicine').filter(quantity__gt=0)

        expired_batches = []  # batches whose expiry date has already passed
        expiring_batches = []  # batches expiring within the next 30 days
        for batch in batches:
            if batch.is_expired:
                expired_batches.append(batch)
            elif batch.is_expiring_soon:
                expiring_batches.append(batch)

        if not expired_batches and not expiring_batches:
            # nothing to report, so don't send an empty email
            self.stdout.write('No expired or expiring stock batches found.')
            return

        send_expiry_alert_admin_email(expired_batches, expiring_batches)  # email the admin the digest
        self.stdout.write(
            f'Sent expiry alert email: {len(expired_batches)} expired, {len(expiring_batches)} expiring soon.'
        )
