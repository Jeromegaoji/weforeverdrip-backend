import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weforeverdrip_backend.settings')
django.setup()

from users.models import User

# Create superuser if it doesn't exist
if not User.objects.filter(email='admin@weforeverdrip.com').exists():
    User.objects.create_superuser(
        email='admin@weforeverdrip.com',
        first_name='Admin',
        last_name='User',
        password='admin123'
    )
    print("✓ Superuser created: admin@weforeverdrip.com / admin123")
else:
    print("✓ Superuser already exists")
