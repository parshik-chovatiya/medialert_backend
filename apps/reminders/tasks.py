# apps/reminders/tasks.py
import logging
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from apps.reminders.models import Reminder, DoseSchedule
from apps.notifications.models import NotificationLog
from apps.notifications.services import NotificationDispatcher

logger = logging.getLogger(__name__)


@shared_task(name='apps.reminders.tasks.send_dose_reminders')
def send_dose_reminders():
    """
    Celery task to send dose reminders at scheduled times.
    Runs every minute via Celery Beat.
    """
    logger.info("Starting dose reminder task...")
    
    try:
        # Get current UTC time
        now_utc = timezone.now()
        current_time_utc = now_utc.time()
        
        # Get all active reminders
        active_reminders = Reminder.objects.filter(
            is_active=True,
            quantity__gt=0,
            start_date__lte=now_utc.date()
        ).select_related('user').prefetch_related('dose_schedules')
        
        notifications_sent = 0
        
        for reminder in active_reminders:
            user = reminder.user
            user_timezone = pytz.timezone(user.timezone)
            
            # Convert current UTC time to user's timezone
            now_user_tz = now_utc.astimezone(user_timezone)
            current_time_user = now_user_tz.time()
            
            # Get all dose schedules for this reminder
            for dose_schedule in reminder.dose_schedules.all():
                # Check if current time matches dose schedule time (within 1 minute tolerance)
                dose_time = dose_schedule.time
                
                # Create datetime objects for comparison
                dose_datetime = datetime.combine(now_user_tz.date(), dose_time)
                dose_datetime = user_timezone.localize(dose_datetime)
                
                # Check if we're within 1 minute of the scheduled time
                time_diff = abs((now_user_tz - dose_datetime).total_seconds())
                
                if time_diff <= 60:  # Within 1 minute
                    # Check if notification already sent in the last 2 minutes
                    two_minutes_ago = now_utc - timedelta(minutes=2)
                    recent_notification = NotificationLog.objects.filter(
                        user=user,
                        reminder=reminder,
                        notification_type='dose_reminder',
                        created_at__gte=two_minutes_ago
                    ).exists()
                    
                    if recent_notification:
                        logger.info(f"Notification already sent recently for {reminder.medicine_name} - {user.email}")
                        continue
                    
                    # Send notifications via specified methods
                    notification_methods = reminder.notification_methods
                    results = NotificationDispatcher.send_dose_reminder(
                        user, reminder, dose_schedule, notification_methods
                    )
                    
                    # Log notification results
                    for method, success in results.items():
                        NotificationLog.objects.create(
                            user=user,
                            reminder=reminder,
                            notification_type='dose_reminder',
                            method=method,
                            status='sent' if success else 'failed',
                            sent_at=timezone.now() if success else None,
                            error_message=None if success else 'Failed to send notification'
                        )
                        
                        if success:
                            notifications_sent += 1
                    
                    # Deduct dose amount from quantity (auto inventory management)
                    old_quantity = reminder.quantity
                    reminder.quantity -= dose_schedule.amount
                    reminder.save()
                    
                    # Update linked inventory
                    if hasattr(reminder, 'inventory_items') and reminder.inventory_items.exists():
                        inventory = reminder.inventory_items.first()
                        inventory.current_quantity = reminder.quantity
                        inventory.save()
                    
                    logger.info(
                        f"Dose reminder sent for {reminder.medicine_name} to {user.email}. "
                        f"Quantity: {old_quantity} -> {reminder.quantity}"
                    )
                    
                    # Check if refill reminder should be sent
                    if reminder.refill_reminder and not reminder.refill_reminder_sent:
                        if reminder.refill_threshold and reminder.quantity <= reminder.refill_threshold:
                            send_refill_reminder_task.delay(reminder.id)
        
        logger.info(f"Dose reminder task completed. {notifications_sent} notifications sent.")
        return f"Sent {notifications_sent} notifications"
        
    except Exception as e:
        logger.error(f"Error in send_dose_reminders task: {str(e)}", exc_info=True)
        raise


@shared_task(name='apps.reminders.tasks.send_refill_reminder_task')
def send_refill_reminder_task(reminder_id):
    """
    Celery task to send refill reminder for a specific reminder.
    """
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        
        # Check if refill reminder already sent
        if reminder.refill_reminder_sent:
            logger.info(f"Refill reminder already sent for {reminder.medicine_name}")
            return "Refill reminder already sent"
        
        user = reminder.user
        notification_methods = reminder.notification_methods
        
        # Send refill notifications
        results = NotificationDispatcher.send_refill_reminder(
            user, reminder, notification_methods
        )
        
        # Log notification results
        for method, success in results.items():
            NotificationLog.objects.create(
                user=user,
                reminder=reminder,
                notification_type='refill_reminder',
                method=method,
                status='sent' if success else 'failed',
                sent_at=timezone.now() if success else None,
                error_message=None if success else 'Failed to send notification'
            )
        
        # Mark refill reminder as sent
        reminder.refill_reminder_sent = True
        reminder.save()
        
        logger.info(f"Refill reminder sent for {reminder.medicine_name} to {user.email}")
        return "Refill reminder sent successfully"
        
    except Reminder.DoesNotExist:
        logger.error(f"Reminder with id {reminder_id} does not exist")
        return "Reminder not found"
    except Exception as e:
        logger.error(f"Error in send_refill_reminder_task: {str(e)}", exc_info=True)
        raise


@shared_task(name='apps.reminders.tasks.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Celery task to cleanup old notification logs (older than 90 days).
    Can be scheduled to run daily.
    """
    try:
        ninety_days_ago = timezone.now() - timedelta(days=90)
        deleted_count = NotificationLog.objects.filter(
            created_at__lt=ninety_days_ago
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notification logs")
        return f"Deleted {deleted_count} old notifications"
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_notifications task: {str(e)}", exc_info=True)
        raise


@shared_task(name='apps.reminders.tasks.deactivate_empty_reminders')
def deactivate_empty_reminders():
    """
    Celery task to deactivate reminders with zero quantity.
    Can be scheduled to run hourly.
    """
    try:
        reminders_to_deactivate = Reminder.objects.filter(
            is_active=True,
            quantity__lte=0
        )
        
        count = reminders_to_deactivate.count()
        reminders_to_deactivate.update(is_active=False)
        
        logger.info(f"Deactivated {count} reminders with zero quantity")
        return f"Deactivated {count} reminders"
        
    except Exception as e:
        logger.error(f"Error in deactivate_empty_reminders task: {str(e)}", exc_info=True)
        raise