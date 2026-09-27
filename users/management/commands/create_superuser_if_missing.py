import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Idempotently create (or repair) the Django superuser from "
        "DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD / "
        "DJANGO_SUPERUSER_FIRST_NAME / DJANGO_SUPERUSER_LAST_NAME "
        "environment variables. Safe to run on every deploy via "
        "fly.toml's release_command — it never errors if the user "
        "already exists."
    )

    def handle(self, *args, **options):
        User = get_user_model()

        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin')
        last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'WFD')

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD not set '
                '— skipping superuser creation this release.'
            ))
            return

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': True,
                'is_superuser': True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser created: {email}'))
            return

        # Already exists — self-heal flags/password in case a secret
        # rotation or manual edit knocked something out of sync.
        changed = False
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.check_password(password):
            user.set_password(password)
            changed = True

        if changed:
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser updated: {email}'))
        else:
            self.stdout.write(f'Superuser already up to date: {email}')