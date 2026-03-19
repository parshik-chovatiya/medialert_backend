# apps/notifications/models.py
from django.db import models
from apps.users.models import CustomUser
from apps.reminders.models import Reminder


class NotificationLog(models.Model):
    """Log of all sent notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('dose_reminder', 'Dose Reminder'),
        ('refill_reminder', 'Refill Reminder'),
    ]
    
    METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push_notification', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notification_logs',
        db_index=True
    )
    reminder = models.ForeignKey(
        Reminder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notification_logs'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'notifications_notificationlog'
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['notification_type', 'method']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.method} - {self.status}"