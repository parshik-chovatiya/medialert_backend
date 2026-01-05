import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')
django.setup()

from django.conf import settings
from twilio.rest import Client

try:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    message = client.messages.create(
        body="Test SMS from Medicine Reminder App!",
        from_=settings.TWILIO_PHONE_NUMBER,
        to="+918799524622"  # Replace with your phone number
    )
    
    print(f"✅ SMS sent successfully! SID: {message.sid}")
except Exception as e:
    print(f"❌ SMS failed: {e}")