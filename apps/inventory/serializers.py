# apps/inventory/serializers.py
from rest_framework import serializers
from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for inventory management"""
    is_expired = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    linked_reminder_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'medicine_name', 'medicine_type', 'current_quantity', 'unit',
            'expiry_date', 'purchase_date', 'price', 'supplier', 'notes',
            'is_active', 'is_expired', 'is_low_stock', 'linked_reminder_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_is_low_stock(self, obj):
        return obj.is_low_stock()
    
    def get_linked_reminder_name(self, obj):
        if obj.reminder:
            return obj.reminder.medicine_name
        return None
    
    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def validate_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_expiry_date(self, value):
        from datetime import date
        if value and value < date.today():
            raise serializers.ValidationError("Cannot add expired medicine to inventory.")
        return value


class InventoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing inventory"""
    is_expired = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'medicine_name', 'medicine_type', 'current_quantity', 
            'unit', 'expiry_date', 'is_active', 'is_expired', 'is_low_stock'
        ]
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_is_low_stock(self, obj):
        return obj.is_low_stock()


class InventoryAdjustSerializer(serializers.Serializer):
    """Serializer for manual inventory quantity adjustment"""
    adjustment = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text="Positive value to add, negative to subtract"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Reason for adjustment"
    )
    
    def validate_adjustment(self, value):
        if value == 0:
            raise serializers.ValidationError("Adjustment value cannot be zero.")
        return value
    
    def validate(self, attrs):
        inventory = self.context.get('inventory')
        adjustment = attrs['adjustment']
        
        # Check if adjustment would result in negative quantity
        new_quantity = inventory.current_quantity + adjustment
        if new_quantity < 0:
            raise serializers.ValidationError({
                'adjustment': f"Adjustment would result in negative quantity. Current: {inventory.current_quantity}"
            })
        
        return attrs


class InventoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for manual inventory creation (not linked to reminder)"""
    
    class Meta:
        model = Inventory
        fields = [
            'medicine_name', 'medicine_type', 'current_quantity', 'unit',
            'expiry_date', 'purchase_date', 'price', 'supplier', 'notes'
        ]
    
    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value
    
    def validate_expiry_date(self, value):
        from datetime import date
        if value and value < date.today():
            raise serializers.ValidationError("Cannot add expired medicine to inventory.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        inventory = Inventory.objects.create(user=user, **validated_data)
        return inventory