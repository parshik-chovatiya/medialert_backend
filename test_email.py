import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

try:
    result = send_mail(
        subject='Test Email - Medicine Reminder',
        message='If you receive this email, the configuration is working correctly!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['testmagento111@gmail.com'],
        fail_silently=False,
    )
    print(f"✅ Email sent successfully! Result: {result}")
except Exception as e:
    print(f"hello")