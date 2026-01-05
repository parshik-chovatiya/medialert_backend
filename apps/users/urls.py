from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/token/refresh/', views.refresh_token_view, name='token_refresh'),
    path('auth/me/', views.current_user_view, name='current_user'),
    
    # Onboarding
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('onboarding/status/', views.onboarding_status_view, name='onboarding_status'),
    
    # Profile Management
    path('profile/update/', views.UserUpdateView.as_view(), name='profile_update'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
]