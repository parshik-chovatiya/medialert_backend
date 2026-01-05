from django.db import models
from apps.users.models import CustomUser
from apps.reminders.models import Reminder


class Inventory(models.Model):
    """Medicine inventory management"""
    
    MEDICINE_TYPE_CHOICES = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('injection', 'Injection'),
        ('syrup', 'Syrup'),
    ]
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='inventories',
        db_index=True
    )
    reminder = models.ForeignKey(
        Reminder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        help_text='Linked reminder for auto-management'
    )
    medicine_name = models.CharField(max_length=255, db_index=True)
    medicine_type = models.CharField(max_length=20, choices=MEDICINE_TYPE_CHOICES)
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Current stock quantity'
    )
    unit = models.CharField(
        max_length=50,
        default='tablets',
        help_text='Unit of measurement (tablets, ml, units, etc.)'
    )
    expiry_date = models.DateField(null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Purchase price'
    )
    supplier = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'medicine_name']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.medicine_name} - {self.current_quantity} {self.unit}"
    
    def is_expired(self):
        """Check if medicine is expired"""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False
    
    def is_low_stock(self, threshold=10):
        """Check if stock is low"""
        return self.current_quantity <= threshold