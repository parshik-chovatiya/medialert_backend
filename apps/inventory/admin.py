from django.contrib import admin
from .models import Inventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'user', 'current_quantity', 'unit', 'expiry_date', 'is_active']
    list_filter = ['medicine_type', 'is_active', 'expiry_date']
    search_fields = ['medicine_name', 'user__email', 'supplier']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'reminder', 'medicine_name', 'medicine_type')
        }),
        ('Quantity', {
            'fields': ('current_quantity', 'unit')
        }),
        ('Purchase Details', {
            'fields': ('purchase_date', 'expiry_date', 'price', 'supplier', 'notes')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )