import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_reminder.settings')
django.setup()

import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

try:
    # Initialize Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    
    # Test token (you'll get this from your mobile app)
    test_token = "your_device_token_here"
    
    # Create message
    message = messaging.Message(
        notification=messaging.Notification(
            title='Test Push Notification',
            body='This is a test from Medicine Reminder!'
        ),
        token=test_token,
    )
    
    # Send message
    response = messaging.send(message)
    print(f"✅ Push notification sent successfully! Response: {response}")
    
except Exception as e:
    print(f"❌ Push notification failed: {e}")