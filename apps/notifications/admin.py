# apps/notifications/admin.py
from django.contrib import admin
from .models import NotificationLog

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'method', 'status', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'method', 'status', 'created_at']
    search_fields = ['user__email', 'error_message']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'reminder', 'notification_type', 'method')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )