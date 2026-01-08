# apps/notifications/serializers.py
from rest_framework import serializers
from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    reminder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'user_email', 'reminder_name', 'notification_type',
            'method', 'status', 'sent_at', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_reminder_name(self, obj):
        if obj.reminder:
            return obj.reminder.medicine_name
        return None


class NotificationLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing notification logs"""
    reminder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'reminder_name', 'notification_type', 
            'method', 'status', 'sent_at', 'created_at'
        ]
    
    def get_reminder_name(self, obj):
        if obj.reminder:
            return obj.reminder.medicine_name
        return None


class NotificationLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notification logs (internal use)"""
    
    class Meta:
        model = NotificationLog
        fields = [
            'user', 'reminder', 'notification_type', 
            'method', 'status', 'sent_at', 'error_message'
        ]
    
    def create(self, validated_data):
        return NotificationLog.objects.create(**validated_data)