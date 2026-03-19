# apps/reminders/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import CustomUser


class Reminder(models.Model):
    """Medicine reminder with dose schedules"""
    
    MEDICINE_TYPE_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('injection', 'Injection'),
        ('syrup', 'Syrup'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reminders', db_index=True)
    medicine_name = models.CharField(max_length=255)
    medicine_type = models.CharField(max_length=20, choices=MEDICINE_TYPE_CHOICES)
    dose_count_daily = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Number of doses per day (1-10)'
    )
    notification_methods = models.JSONField(
        default=list,
        help_text='List of notification methods: email, sms, push_notification'
    )
    start_date = models.DateField()
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Current quantity of medicine'
    )
    initial_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Initial quantity when reminder was created'
    )
    refill_reminder = models.BooleanField(default=False)
    refill_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Quantity threshold to trigger refill reminder'
    )
    refill_reminder_sent = models.BooleanField(
        default=False,
        help_text='Flag to track if refill reminder has been sent'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminders_reminder'
        verbose_name = 'Reminder'
        verbose_name_plural = 'Reminders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['start_date']),
        ]
    
    def __str__(self):
        return f"{self.medicine_name} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Set initial_quantity on creation
        if not self.pk:
            self.initial_quantity = self.quantity
        
        # Auto-reset refill_reminder_sent if quantity goes above threshold
        if self.refill_threshold and self.quantity > self.refill_threshold:
            self.refill_reminder_sent = False
        
        # Deactivate reminder if quantity is 0
        if self.quantity <= 0:
            self.is_active = False
        
        super().save(*args, **kwargs)


class DoseSchedule(models.Model):
    """Individual dose schedule for a reminder"""
    
    reminder = models.ForeignKey(
        Reminder,
        on_delete=models.CASCADE,
        related_name='dose_schedules'
    )
    dose_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='Dose number (1-10)'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount of medicine per dose (tablets/ml/units)'
    )
    time = models.TimeField(help_text='Time to take the dose')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminders_doseschedule'
        verbose_name = 'Dose Schedule'
        verbose_name_plural = 'Dose Schedules'
        ordering = ['reminder', 'dose_number']
        unique_together = [['reminder', 'dose_number']]
        indexes = [
            models.Index(fields=['reminder', 'time']),
        ]
    
    def __str__(self):
        return f"Dose {self.dose_number} - {self.reminder.medicine_name} at {self.time}"