from django.contrib import admin
from .models import HealthTip

@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content', 'source']
