from django.contrib import admin
from .models import Reminder, DoseSchedule

class DoseScheduleInline(admin.TabularInline):
    model = DoseSchedule
    extra = 1
    fields = ['dose_number', 'amount', 'time']

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'user', 'medicine_type', 'dose_count_daily', 'quantity', 'is_active', 'created_at']
    list_filter = ['medicine_type', 'is_active', 'refill_reminder', 'created_at']
    search_fields = ['medicine_name', 'user__email']
    inlines = [DoseScheduleInline]
    readonly_fields = ['initial_quantity', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'medicine_name', 'medicine_type', 'dose_count_daily')
        }),
        ('Schedule', {
            'fields': ('start_date', 'notification_methods')
        }),
        ('Quantity Management', {
            'fields': ('quantity', 'initial_quantity', 'refill_reminder', 'refill_threshold', 'refill_reminder_sent')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )