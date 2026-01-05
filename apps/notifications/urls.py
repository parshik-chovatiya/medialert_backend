from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

router = DefaultRouter()
router.register(r'logs', views.NotificationLogViewSet, basename='notification-log')

urlpatterns = [
    path('', include(router.urls)),
]