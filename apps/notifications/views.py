# apps/notifications/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from .models import NotificationLog
from .serializers import NotificationLogSerializer, NotificationLogListSerializer, DeviceTokenSerializer
from utils.responses import StandardResponse


class RegisterDeviceTokenView(generics.GenericAPIView):
    """Register, update, or unregister FCM device token for Android push notifications."""

    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Register an FCM device token for the authenticated user."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request.user.device_token = serializer.validated_data['token']
            request.user.save(update_fields=['device_token'])
            return StandardResponse.success(message='Device token registered successfully')

        error_message = '; '.join(
            [f"{k}: {', '.join(v)}" for k, v in serializer.errors.items()]
        )
        return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Refresh / update the FCM device token for the authenticated user."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request.user.device_token = serializer.validated_data['token']
            request.user.save(update_fields=['device_token'])
            return StandardResponse.success(message='Device token updated successfully')

        error_message = '; '.join(
            [f"{k}: {', '.join(v)}" for k, v in serializer.errors.items()]
        )
        return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Clear the FCM device token for the authenticated user."""
        request.user.device_token = None
        request.user.save(update_fields=['device_token'])
        return StandardResponse.success(message='Device token unregistered successfully')


class SendTestPushView(APIView):
    """
    Send a test push notification to the authenticated user's registered device.
    Useful during development to verify FCM connectivity.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.device_token:
            return StandardResponse.error(
                message='No device token registered for this user. '
                        'POST to /notifications/device-token/ first.',
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services import _init_firebase
            from firebase_admin import messaging

            if not _init_firebase():
                return StandardResponse.error(
                    message='Firebase is not configured on the server.',
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 Medialert Test',
                    body='Push notifications are working correctly!',
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='medialert_reminders',
                        sound='default',
                        priority='high',
                        color='#2196F3',
                    ),
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title='🔔 Medialert Test',
                        body='Push notifications are working correctly!',
                        icon='/logo.png',
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link='/',
                    )
                ),
                data={
                    'type': 'test',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                },
                token=user.device_token,
            )

            response = messaging.send(message)
            return StandardResponse.success(
                message='Test push notification sent successfully',
                data={'fcm_message_id': response},
            )

        except Exception as e:
            return StandardResponse.error(
                message=f'Failed to send test push: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notification logs (read-only)"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notification logs for current user only"""
        return NotificationLog.objects.filter(user=self.request.user).select_related('reminder')
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return NotificationLogListSerializer
        return NotificationLogSerializer
    
    def list(self, request, *args, **kwargs):
        """List all notification logs with filtering"""
        queryset = self.get_queryset()
        
        # Filter by notification type
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by method
        method = request.query_params.get('method')
        if method:
            queryset = queryset.filter(method=method)
        
        # Filter by status
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date_obj = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__gte=start_date_obj)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date_obj = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__lte=end_date_obj)
            except ValueError:
                pass
        
        # Pagination
        page_size = int(request.query_params.get('page_size', 50))
        page = int(request.query_params.get('page', 1))
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        total_count = queryset.count()
        paginated_queryset = queryset[start_index:end_index]
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        return StandardResponse.success(data={
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'logs': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Get single notification log details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return StandardResponse.success(data={'log': serializer.data})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications (last 7 days)"""
        seven_days_ago = timezone.now() - timedelta(days=7)
        queryset = self.get_queryset().filter(created_at__gte=seven_days_ago)
        
        serializer = NotificationLogListSerializer(queryset, many=True)
        return StandardResponse.success(data={
            'count': queryset.count(),
            'logs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get all failed notifications"""
        queryset = self.get_queryset().filter(status='failed')
        
        serializer = NotificationLogListSerializer(queryset, many=True)
        return StandardResponse.success(data={
            'count': queryset.count(),
            'logs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics"""
        queryset = self.get_queryset()
        
        # Overall stats
        total_notifications = queryset.count()
        sent_count = queryset.filter(status='sent').count()
        failed_count = queryset.filter(status='failed').count()
        pending_count = queryset.filter(status='pending').count()
        
        # By notification type
        dose_reminders = queryset.filter(notification_type='dose_reminder').count()
        refill_reminders = queryset.filter(notification_type='refill_reminder').count()
        
        # By method
        email_count = queryset.filter(method='email').count()
        sms_count = queryset.filter(method='sms').count()
        push_count = queryset.filter(method='push_notification').count()
        
        # Recent (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_count = queryset.filter(created_at__gte=seven_days_ago).count()
        
        # Today
        today = timezone.now().date()
        today_count = queryset.filter(created_at__date=today).count()
        
        return StandardResponse.success(data={
            'total_notifications': total_notifications,
            'by_status': {
                'sent': sent_count,
                'failed': failed_count,
                'pending': pending_count
            },
            'by_type': {
                'dose_reminder': dose_reminders,
                'refill_reminder': refill_reminders
            },
            'by_method': {
                'email': email_count,
                'sms': sms_count,
                'push_notification': push_count
            },
            'timeframe': {
                'today': today_count,
                'last_7_days': recent_count
            }
        })