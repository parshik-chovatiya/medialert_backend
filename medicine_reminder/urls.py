# medicine_reminder/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Medicine Reminder API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'auth': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'refresh_token': '/api/auth/token/refresh/',
                'current_user': '/api/auth/me/',
            },
            'onboarding': {
                'complete': '/api/onboarding/',
                'status': '/api/onboarding/status/',
            },
            'profile': {
                'update': '/api/profile/update/',
                'change_password': '/api/profile/change-password/',
            },
            'reminders': {
                'list': '/api/reminders/',
                'create': '/api/reminders/',
                'detail': '/api/reminders/{id}/',
                'update': '/api/reminders/{id}/',
                'delete': '/api/reminders/{id}/',
                'deactivate': '/api/reminders/{id}/deactivate/',
                'activate': '/api/reminders/{id}/activate/',
                'update_quantity': '/api/reminders/{id}/update_quantity/',
                'today_schedule': '/api/reminders/today_schedule/',
            },
            'inventory': {
                'list': '/api/inventory/',
                'create': '/api/inventory/',
                'detail': '/api/inventory/{id}/',
                'update': '/api/inventory/{id}/',
                'delete': '/api/inventory/{id}/',
                'adjust': '/api/inventory/{id}/adjust/',
                'low_stock': '/api/inventory/low_stock/',
                'expired': '/api/inventory/expired/',
                'expiring_soon': '/api/inventory/expiring_soon/',
            },
            'notifications': {
                'list': '/api/notifications/logs/',
                'detail': '/api/notifications/logs/{id}/',
                'recent': '/api/notifications/logs/recent/',
                'failed': '/api/notifications/logs/failed/',
                'stats': '/api/notifications/logs/stats/',
            }
        }
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Root
    path('api/', api_root, name='api_root'),
    
    # API Endpoints
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.reminders.urls')),
    path('api/', include('apps.inventory.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    
     # API Schema URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional: Swagger UI and ReDoc UI
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]