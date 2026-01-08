# apps/notifications/services.py
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


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
    
    @staticmethod
    def send_dose_reminder(user, reminder, dose_schedule):
        """Send dose reminder push notification"""
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            # Initialize Firebase Admin SDK if not already initialized
            if not firebase_admin._apps:
                if settings.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning("Firebase credentials not configured")
                    return False
            
            # Check if user has device token
            if not user.device_token:
                logger.warning(f"User {user.email} does not have a device token")
                return False
            
            # Create notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Medicine Reminder: {reminder.medicine_name}",
                    body=f"Take {dose_schedule.amount} {reminder.get_medicine_type_display()} at {dose_schedule.time.strftime('%I:%M %p')}"
                ),
                data={
                    'reminder_id': str(reminder.id),
                    'medicine_name': reminder.medicine_name,
                    'dose_amount': str(dose_schedule.amount),
                    'dose_time': dose_schedule.time.strftime('%H:%M:%S'),
                    'type': 'dose_reminder'
                },
                token=user.device_token,
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"Dose reminder push notification sent to {user.email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send dose reminder push notification to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_refill_reminder(user, reminder):
        """Send refill reminder push notification"""
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            # Initialize Firebase Admin SDK if not already initialized
            if not firebase_admin._apps:
                if settings.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                else:
                    logger.warning("Firebase credentials not configured")
                    return False
            
            # Check if user has device token
            if not user.device_token:
                logger.warning(f"User {user.email} does not have a device token")
                return False
            
            # Create notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Refill Alert: {reminder.medicine_name}",
                    body=f"Your medicine stock is low ({reminder.quantity} remaining). Please refill soon."
                ),
                data={
                    'reminder_id': str(reminder.id),
                    'medicine_name': reminder.medicine_name,
                    'current_quantity': str(reminder.quantity),
                    'threshold': str(reminder.refill_threshold),
                    'type': 'refill_reminder'
                },
                token=user.device_token,
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f"Refill reminder push notification sent to {user.email}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send refill reminder push notification to {user.email}: {str(e)}")
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