import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')
django.setup()

from django.conf import settings

print(f"EMAIL_HOST_USER: '{settings.EMAIL_HOST_USER}'")
print(f"DEFAULT_FROM_EMAIL: '{settings.DEFAULT_FROM_EMAIL}'")
print(f"EMAIL_HOST: '{settings.EMAIL_HOST}'")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
