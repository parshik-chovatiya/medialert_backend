# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'is_onboarded', 'is_active', 'created_at']
    list_filter = ['is_onboarded', 'is_active', 'is_staff', 'gender']
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'birthdate', 'gender', 'timezone')}),
        ('Notifications', {'fields': ('device_token',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_onboarded')}),
        ('Important Dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
