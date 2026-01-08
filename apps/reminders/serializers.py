# apps/reminders/serializers.py
from rest_framework import serializers
from .models import Reminder, DoseSchedule
from apps.inventory.models import Inventory


class DoseScheduleSerializer(serializers.ModelSerializer):
    """Serializer for dose schedule"""
    
    class Meta:
        model = DoseSchedule
        fields = ['id', 'dose_number', 'amount', 'time']
        read_only_fields = ['id']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for reminder with dose schedules"""
    dose_schedules = DoseScheduleSerializer(many=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, write_only=True, help_text='Required if SMS notification is selected')
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'medicine_name', 'medicine_type', 'dose_count_daily',
            'notification_methods', 'start_date', 'quantity', 'initial_quantity',
            'refill_reminder', 'refill_threshold', 'refill_reminder_sent',
            'is_active', 'dose_schedules', 'phone_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'initial_quantity', 'refill_reminder_sent', 'is_active', 'created_at', 'updated_at']
    
    def validate_notification_methods(self, value):
        valid_methods = ['email', 'sms', 'push_notification']
        if not value:
            raise serializers.ValidationError("At least one notification method is required.")
        for method in value:
            if method not in valid_methods:
                raise serializers.ValidationError(f"Invalid notification method: {method}")
        return value
    
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def validate_refill_threshold(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Refill threshold cannot be negative.")
        return value
    
    def validate(self, attrs):
        # Validate dose_schedules count matches dose_count_daily
        dose_schedules = attrs.get('dose_schedules', [])
        dose_count_daily = attrs.get('dose_count_daily')
        
        if len(dose_schedules) != dose_count_daily:
            raise serializers.ValidationError({
                'dose_schedules': f"Number of dose schedules ({len(dose_schedules)}) must match dose_count_daily ({dose_count_daily})."
            })
        
        # Validate refill_threshold if refill_reminder is enabled
        if attrs.get('refill_reminder') and not attrs.get('refill_threshold'):
            raise serializers.ValidationError({
                'refill_threshold': "Refill threshold is required when refill reminder is enabled."
            })
        
        # Validate phone_number if SMS is selected
        notification_methods = attrs.get('notification_methods', [])
        phone_number = attrs.get('phone_number')
        
        if 'sms' in notification_methods and not phone_number:
            raise serializers.ValidationError({
                'phone_number': "Phone number is required when SMS notification is selected."
            })
        
        return attrs
    
    def create(self, validated_data):
        dose_schedules_data = validated_data.pop('dose_schedules')
        phone_number = validated_data.pop('phone_number', None)
        user = self.context['request'].user
        
        # Save phone number to user if SMS is selected
        if phone_number and 'sms' in validated_data.get('notification_methods', []):
            user.phone_number = phone_number
            user.save()
        
        # Create reminder
        reminder = Reminder.objects.create(user=user, **validated_data)
        
        # Create dose schedules
        for dose_data in dose_schedules_data:
            DoseSchedule.objects.create(reminder=reminder, **dose_data)
        
        # Auto-create inventory entry
        Inventory.objects.create(
            user=user,
            reminder=reminder,
            medicine_name=reminder.medicine_name,
            medicine_type=reminder.medicine_type,
            current_quantity=reminder.quantity,
            unit='tablets' if reminder.medicine_type in ['tablet', 'capsule'] else 'ml'
        )
        
        return reminder
    
    def update(self, instance, validated_data):
        dose_schedules_data = validated_data.pop('dose_schedules', None)
        phone_number = validated_data.pop('phone_number', None)
        user = self.context['request'].user
        
        # Update phone number if SMS is selected
        if phone_number and 'sms' in validated_data.get('notification_methods', instance.notification_methods):
            user.phone_number = phone_number
            user.save()
        
        # Update reminder fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update dose schedules if provided
        if dose_schedules_data is not None:
            # Delete old dose schedules
            instance.dose_schedules.all().delete()
            
            # Create new dose schedules
            for dose_data in dose_schedules_data:
                DoseSchedule.objects.create(reminder=instance, **dose_data)
        
        # Update linked inventory
        if hasattr(instance, 'inventory_items') and instance.inventory_items.exists():
            inventory = instance.inventory_items.first()
            inventory.current_quantity = instance.quantity
            inventory.medicine_name = instance.medicine_name
            inventory.medicine_type = instance.medicine_type
            inventory.save()
        
        return instance


class ReminderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reminders"""
    dose_count = serializers.SerializerMethodField()
    next_dose_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Reminder
        fields = [
            'id', 'medicine_name', 'medicine_type', 'dose_count_daily',
            'quantity', 'is_active', 'dose_count', 'next_dose_time', 'created_at'
        ]
    
    def get_dose_count(self, obj):
        return obj.dose_schedules.count()
    
    def get_next_dose_time(self, obj):
        from django.utils import timezone
        import pytz
        
        # Get user's timezone
        user_timezone = pytz.timezone(obj.user.timezone)
        
        # Convert current UTC time to user's timezone
        now_user_tz = timezone.now().astimezone(user_timezone).time()
        
        # Find next dose after current time in user's timezone
        next_dose = obj.dose_schedules.filter(time__gt=now_user_tz).order_by('time').first()
        if next_dose:
            return next_dose.time
        
        # If no dose found for today, return first dose of tomorrow
        first_dose = obj.dose_schedules.order_by('time').first()
        return first_dose.time if first_dose else None