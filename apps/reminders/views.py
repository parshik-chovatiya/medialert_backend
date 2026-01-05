from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Reminder, DoseSchedule
from .serializers import ReminderSerializer, ReminderListSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reminders"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return reminders for current user only"""
        return Reminder.objects.filter(user=self.request.user).prefetch_related('dose_schedules')
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return ReminderListSerializer
        return ReminderSerializer
    
    def list(self, request, *args, **kwargs):
        """List all reminders for current user"""
        queryset = self.get_queryset()
        
        # Optional filtering
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        medicine_type = request.query_params.get('medicine_type')
        if medicine_type:
            queryset = queryset.filter(medicine_type=medicine_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs):
        """Create new reminder with dose schedules"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            reminder = serializer.save()
            return Response({
                'message': 'Reminder created successfully',
                'data': ReminderSerializer(reminder).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get single reminder details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Update reminder (full update)"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            reminder = serializer.save()
            return Response({
                'message': 'Reminder updated successfully',
                'data': ReminderSerializer(reminder).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update reminder"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete reminder"""
        instance = self.get_object()
        
        # Also delete linked inventory if exists
        if hasattr(instance, 'inventory_items'):
            instance.inventory_items.all().delete()
        
        instance.delete()
        return Response({
            'message': 'Reminder deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a reminder without deleting"""
        reminder = self.get_object()
        reminder.is_active = False
        reminder.save()
        
        return Response({
            'message': 'Reminder deactivated successfully',
            'data': ReminderSerializer(reminder).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a reminder"""
        reminder = self.get_object()
        
        # Check if quantity is available
        if reminder.quantity <= 0:
            return Response({
                'error': 'Cannot activate reminder with zero quantity. Please update quantity first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reminder.is_active = True
        reminder.save()
        
        return Response({
            'message': 'Reminder activated successfully',
            'data': ReminderSerializer(reminder).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """Update reminder quantity manually (e.g., after refill)"""
        reminder = self.get_object()
        new_quantity = request.data.get('quantity')
        
        if new_quantity is None:
            return Response({
                'error': 'Quantity is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_quantity = float(new_quantity)
            if new_quantity < 0:
                return Response({
                    'error': 'Quantity cannot be negative'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid quantity value'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update reminder quantity
        old_quantity = reminder.quantity
        reminder.quantity = new_quantity
        reminder.save()
        
        # Update linked inventory
        if hasattr(reminder, 'inventory_items') and reminder.inventory_items.exists():
            inventory = reminder.inventory_items.first()
            inventory.current_quantity = new_quantity
            inventory.save()
        
        return Response({
            'message': 'Quantity updated successfully',
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'data': ReminderSerializer(reminder).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard data for selected date with dynamic quantity calculation"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        from collections import defaultdict
        from decimal import Decimal
        
        # Get date parameter (default to today)
        date_param = request.query_params.get('date')
        
        if date_param:
            try:
                selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            selected_date = timezone.now().date()
        
        # Validate date range (today to +15 days)
        today = timezone.now().date()
        max_date = today + timedelta(days=15)
        
        if selected_date < today:
            return Response({
                'error': 'Cannot select past dates'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if selected_date > max_date:
            return Response({
                'error': 'Cannot select dates beyond 15 days from today'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all reminders that were active at some point
        reminders = Reminder.objects.filter(
            user=self.request.user,
            start_date__lte=selected_date
        ).prefetch_related('dose_schedules')
        
        # Calculate available reminders for selected date
        doses_by_time = defaultdict(list)
        total_doses = 0
        active_reminder_count = 0
        
        for reminder in reminders:
            # Calculate days passed since start
            days_passed = (selected_date - reminder.start_date).days
            
            if days_passed < 0:
                # Reminder hasn't started yet
                continue
            
            # Calculate total doses consumed until selected date
            total_daily_amount = sum(
                Decimal(str(dose.amount)) 
                for dose in reminder.dose_schedules.all()
            )
            
            total_consumed = total_daily_amount * days_passed
            
            # Calculate remaining quantity for selected date
            remaining_quantity = reminder.initial_quantity - total_consumed
            
            # Skip if quantity would be zero or negative on selected date
            if remaining_quantity <= 0:
                continue
            
            # This reminder is still active on selected date
            active_reminder_count += 1
            
            for dose in reminder.dose_schedules.all():
                doses_by_time[dose.time].append({
                    'reminder_id': reminder.id,
                    'medicine_name': reminder.medicine_name,
                    'medicine_type': reminder.medicine_type,
                    'amount': str(dose.amount),
                    'dose_number': dose.dose_number,
                    'notification_methods': reminder.notification_methods,
                    'quantity_remaining': str(remaining_quantity),
                    'is_active': True
                })
                total_doses += 1
        
        # Sort by time and format response
        sorted_doses = []
        for time_slot in sorted(doses_by_time.keys()):
            sorted_doses.append({
                'time': str(time_slot),
                'reminders': doses_by_time[time_slot]
            })
        
        # Get day name
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[selected_date.weekday()]
        
        return Response({
            'selected_date': str(selected_date),
            'day_name': day_name,
            'total_doses': total_doses,
            'total_reminders': active_reminder_count,
            'doses': sorted_doses,
            'date_range': {
                'min_date': str(today),
                'max_date': str(max_date),
                'available_dates': [
                    str(today + timedelta(days=i)) for i in range(16)
                ]
            }
        }, status=status.HTTP_200_OK)