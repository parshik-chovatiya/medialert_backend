from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Inventory
from .serializers import (
    InventorySerializer,
    InventoryListSerializer,
    InventoryAdjustSerializer,
    InventoryCreateSerializer
)


class InventoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing inventory"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return inventory for current user only"""
        return Inventory.objects.filter(user=self.request.user).select_related('reminder')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return InventoryListSerializer
        elif self.action == 'create':
            return InventoryCreateSerializer
        return InventorySerializer
    
    def list(self, request, *args, **kwargs):
        """List all inventory items"""
        queryset = self.get_queryset()
        
        # Optional filtering
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        medicine_type = request.query_params.get('medicine_type')
        if medicine_type:
            queryset = queryset.filter(medicine_type=medicine_type)
        
        # Filter low stock items
        low_stock = request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = [item for item in queryset if item.is_low_stock()]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': len(serializer.data) if isinstance(queryset, list) else queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Create manual inventory entry (not linked to reminder)"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            inventory = serializer.save()
            return Response({
                'message': 'Inventory created successfully',
                'data': InventorySerializer(inventory).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get single inventory details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update inventory"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # If inventory is linked to reminder, sync quantity
        if instance.reminder and 'current_quantity' in request.data:
            instance.reminder.quantity = request.data['current_quantity']
            instance.reminder.save()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            inventory = serializer.save()
            return Response({
                'message': 'Inventory updated successfully',
                'data': InventorySerializer(inventory).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update inventory"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete inventory"""
        instance = self.get_object()
        
        # Check if linked to active reminder
        if instance.reminder and instance.reminder.is_active:
            return Response({
                'error': 'Cannot delete inventory linked to active reminder. Deactivate reminder first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response({
            'message': 'Inventory deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """Manually adjust inventory quantity"""
        inventory = self.get_object()
        serializer = InventoryAdjustSerializer(
            data=request.data,
            context={'inventory': inventory}
        )
        
        if serializer.is_valid():
            adjustment = serializer.validated_data['adjustment']
            notes = serializer.validated_data.get('notes', '')
            
            old_quantity = inventory.current_quantity
            new_quantity = old_quantity + adjustment
            
            # Update inventory
            inventory.current_quantity = new_quantity
            if notes:
                inventory.notes = f"{inventory.notes or ''}\n[{timezone.now()}] Adjusted by {adjustment}: {notes}".strip()
            inventory.save()
            
            # Update linked reminder if exists
            if inventory.reminder:
                inventory.reminder.quantity = new_quantity
                inventory.reminder.save()
            
            return Response({
                'message': 'Inventory adjusted successfully',
                'old_quantity': old_quantity,
                'adjustment': adjustment,
                'new_quantity': new_quantity,
                'data': InventorySerializer(inventory).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock items"""
        queryset = self.get_queryset().filter(is_active=True)
        low_stock_items = [item for item in queryset if item.is_low_stock()]
        
        serializer = InventoryListSerializer(low_stock_items, many=True)
        return Response({
            'count': len(low_stock_items),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get all expired items"""
        queryset = self.get_queryset().filter(is_active=True)
        expired_items = [item for item in queryset if item.is_expired()]
        
        serializer = InventoryListSerializer(expired_items, many=True)
        return Response({
            'count': len(expired_items),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get items expiring within 30 days"""
        from datetime import timedelta
        
        queryset = self.get_queryset().filter(is_active=True, expiry_date__isnull=False)
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        expiring_soon = queryset.filter(
            expiry_date__gte=today,
            expiry_date__lte=thirty_days_later
        )
        
        serializer = InventoryListSerializer(expiring_soon, many=True)
        return Response({
            'count': expiring_soon.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)