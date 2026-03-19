    # apps/notifications/services.py
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def _init_firebase():
    """Initialize Firebase Admin SDK once (singleton pattern)."""
    import firebase_admin
    from firebase_admin import credentials

    if not firebase_admin._apps:
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        if not cred_path:
            logger.warning("FIREBASE_CREDENTIALS_PATH is not set in settings")
            return False
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")
    return True


class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_dose_reminder(user, reminder, dose_schedule):
        """Send dose reminder email"""
        try:
            subject = f"Medicine Reminder: {reminder.medicine_name}"
            message = f"""
                Hello {user.name or user.email},

                This is a reminder to take your medicine:

                Medicine: {reminder.medicine_name}
                Type: {reminder.get_medicine_type_display()}
                Amount: {dose_schedule.amount}
                Time: {dose_schedule.time.strftime('%I:%M %p')}

                Remaining Quantity: {reminder.quantity}

                Best regards,
                Medicine Reminder Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Dose reminder email sent to {user.email} for {reminder.medicine_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send dose reminder email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_refill_reminder(user, reminder):
        """Send refill reminder email"""
        try:
            subject = f"Refill Reminder: {reminder.medicine_name}"
            message = f"""
                Hello {user.name or user.email},

                Your medicine stock is running low!

                Medicine: {reminder.medicine_name}
                Current Quantity: {reminder.quantity}
                Refill Threshold: {reminder.refill_threshold}

                Please refill your medicine soon to avoid running out.

                Best regards,
                Medicine Reminder Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Refill reminder email sent to {user.email} for {reminder.medicine_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send refill reminder email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset_email(user, uid, token):
        """Send password reset email"""
        try:
            subject = "Password Reset Request"
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/')
            reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"
            
            message = f"""
                Hello {user.name or user.email},

                We received a request to reset your password for your Medialert account.
                Please click the link below to choose a new password:

                {reset_url}

                If you didn't request a password reset, you can safely ignore this email.
                The link will expire in 24 hours.

                Best regards,
                Medicine Reminder Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False


class SMSService:
    """Service for sending SMS notifications via Twilio"""
    
    @staticmethod
    def send_dose_reminder(user, reminder, dose_schedule):
        """Send dose reminder SMS"""
        try:
            from twilio.rest import Client
            
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.warning("Twilio credentials not configured")
                return False
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Get user phone number
            phone_number = user.phone_number
            
            if not phone_number:
                logger.warning(f"User {user.email} does not have a phone number")
                return False
            
            message = f"Medicine Reminder: Take {dose_schedule.amount} {reminder.medicine_name} at {dose_schedule.time.strftime('%I:%M %p')}"
            
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"Dose reminder SMS sent to {phone_number} for {reminder.medicine_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send dose reminder SMS to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_refill_reminder(user, reminder):
        """Send refill reminder SMS"""
        try:
            from twilio.rest import Client
            
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.warning("Twilio credentials not configured")
                return False
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            phone_number = user.phone_number
            
            if not phone_number:
                logger.warning(f"User {user.email} does not have a phone number")
                return False
            
            message = f"Refill Alert: Your {reminder.medicine_name} stock is low ({reminder.quantity} remaining). Please refill soon."
            
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"Refill reminder SMS sent to {phone_number} for {reminder.medicine_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send refill reminder SMS to {user.email}: {str(e)}")
            return False


class PushNotificationService:
    """Service for sending push notifications via Firebase FCM"""

    # Android notification channel ID — must match the channel created in the Android app
    ANDROID_CHANNEL_ID = 'medialert_reminders'

    @staticmethod
    def send_dose_reminder(user, reminder, dose_schedule):
        """Send dose reminder push notification with Android high-priority config"""
        try:
            from firebase_admin import messaging

            if not _init_firebase():
                return False

            if not user.device_token:
                logger.warning(f"User {user.email} does not have a device token")
                return False

            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"\U0001f48a Medicine Reminder: {reminder.medicine_name}",
                    body=(
                        f"Time to take {dose_schedule.amount} "
                        f"{reminder.get_medicine_type_display()} "
                        f"at {dose_schedule.time.strftime('%I:%M %p')}"
                    ),
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id=PushNotificationService.ANDROID_CHANNEL_ID,
                        sound='default',
                        priority='high',
                        visibility='public',
                        icon='ic_notification',
                        color='#4CAF50',
                    ),
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=f"\U0001f48a Medicine Reminder: {reminder.medicine_name}",
                        body=(
                            f"Time to take {dose_schedule.amount} "
                            f"{reminder.get_medicine_type_display()} "
                            f"at {dose_schedule.time.strftime('%I:%M %p')}"
                        ),
                        icon="/logo.png",
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=getattr(settings, 'FRONTEND_URL', 'https://localhost:3000/'),
                    )
                ),
                data={
                    'reminder_id': str(reminder.id),
                    'medicine_name': reminder.medicine_name,
                    'dose_amount': str(dose_schedule.amount),
                    'dose_time': dose_schedule.time.strftime('%H:%M:%S'),
                    'type': 'dose_reminder',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                },
                token=user.device_token,
            )

            response = messaging.send(message)
            logger.info(f"Dose reminder push sent to {user.email}: {response}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to send dose reminder push to {user.email}: {str(e)}",
                exc_info=True,
            )
            return False
    
    @staticmethod
    def send_refill_reminder(user, reminder):
        """Send refill reminder push notification with Android high-priority config"""
        try:
            from firebase_admin import messaging

            if not _init_firebase():
                return False

            if not user.device_token:
                logger.warning(f"User {user.email} does not have a device token")
                return False

            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"\u26a0\ufe0f Refill Alert: {reminder.medicine_name}",
                    body=(
                        f"Stock is low ({reminder.quantity} remaining). "
                        f"Refill before it runs out!"
                    ),
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id=PushNotificationService.ANDROID_CHANNEL_ID,
                        sound='default',
                        priority='high',
                        visibility='public',
                        icon='ic_notification',
                        color='#FF9800',
                    ),
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=f"\u26a0\ufe0f Refill Alert: {reminder.medicine_name}",
                        body=(
                            f"Stock is low ({reminder.quantity} remaining). "
                            f"Refill before it runs out!"
                        ),
                        icon="/logo.png",
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=getattr(settings, 'FRONTEND_URL', 'https://localhost:3000/'),
                    )
                ),
                data={
                    'reminder_id': str(reminder.id),
                    'medicine_name': reminder.medicine_name,
                    'current_quantity': str(reminder.quantity),
                    'threshold': str(reminder.refill_threshold),
                    'type': 'refill_reminder',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                },
                token=user.device_token,
            )

            response = messaging.send(message)
            logger.info(f"Refill reminder push sent to {user.email}: {response}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to send refill reminder push to {user.email}: {str(e)}",
                exc_info=True,
            )
            return False


class NotificationDispatcher:
    """Dispatcher to send notifications via multiple methods"""
    
    @staticmethod
    def send_dose_reminder(user, reminder, dose_schedule, methods):
        """Send dose reminder via specified methods"""
        results = {}
        
        if 'email' in methods:
            results['email'] = EmailService.send_dose_reminder(user, reminder, dose_schedule)
        
        if 'sms' in methods:
            results['sms'] = SMSService.send_dose_reminder(user, reminder, dose_schedule)
        
        if 'push_notification' in methods:
            results['push_notification'] = PushNotificationService.send_dose_reminder(user, reminder, dose_schedule)
        
        return results
    
    @staticmethod
    def send_refill_reminder(user, reminder, methods):
        """Send refill reminder via specified methods"""
        results = {}
        
        if 'email' in methods:
            results['email'] = EmailService.send_refill_reminder(user, reminder)
        
        if 'sms' in methods:
            results['sms'] = SMSService.send_refill_reminder(user, reminder)
        
        if 'push_notification' in methods:
            results['push_notification'] = PushNotificationService.send_refill_reminder(user, reminder)
        
        return results  