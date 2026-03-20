import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weforeverdrip_backend.settings_production')
django.setup()

from users.models import User

if not User.objects.filter(email='admin@weforeverdrip.com').exists():
    User.objects.create_superuser(
        email='admin@weforeverdrip.com',
        first_name='Admin',
        last_name='WFD',
        password='03wfd2026!'
    )
    print("Superuser created")
else:
    # Update password in case it was created with wrong password
    user = User.objects.get(email='admin@weforeverdrip.com')
    user.set_password('03wfd2026!')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("Superuser updated")

