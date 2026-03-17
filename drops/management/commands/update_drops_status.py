from django.core.management.base import BaseCommand
from django.utils import timezone
from drops.models import Drop


class Command(BaseCommand):
    help = 'Update drop statuses based on launch_date and end_date.'

    def handle(self, *args, **options):
        now = timezone.now()
        updated = []

        scheduled_to_live = Drop.objects.filter(status='scheduled', launch_date__lte=now)
        for drop in scheduled_to_live:
            drop.status = 'live'
            drop.save(update_fields=['status', 'updated_at'])
            updated.append(f"{drop.slug}: scheduled -> live")

        live_to_ended = Drop.objects.filter(status='live', end_date__isnull=False, end_date__lte=now)
        for drop in live_to_ended:
            drop.status = 'ended'
            drop.save(update_fields=['status', 'updated_at'])
            updated.append(f"{drop.slug}: live -> ended")

        # Also explicitly close scheduled drops that have already passed end_date as ended.
        scheduled_to_ended = Drop.objects.filter(status='scheduled', end_date__isnull=False, end_date__lte=now)
        for drop in scheduled_to_ended:
            drop.status = 'ended'
            drop.save(update_fields=['status', 'updated_at'])
            updated.append(f"{drop.slug}: scheduled -> ended")

        if updated:
            self.stdout.write(self.style.SUCCESS('Updated drop statuses:'))
            for msg in updated:
                self.stdout.write(f' - {msg}')
        else:
            self.stdout.write(self.style.SUCCESS('No drop statuses needed updating.'))
