# apps/notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register(r'logs', views.NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('device-token/', views.RegisterDeviceTokenView.as_view(), name='device-token'),
    path('test-push/', views.SendTestPushView.as_view(), name='test-push'),
    path('', include(router.urls)),
]