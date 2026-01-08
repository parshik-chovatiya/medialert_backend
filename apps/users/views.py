# apps/users/views.py
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import CustomUser
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    OnboardingSerializer,
    UserSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer
)
from utils.responses import StandardResponse


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'user': UserSerializer(user).data
        }
        
        response = StandardResponse.created(
            data=response_data,
            message='User registered successfully'
        )
        
        # Set tokens in HTTP-only cookies
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite='None',
            max_age=900
        )
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='None',
            max_age=604800
        )
        
        return response
    
    # Format error message
    error_message = StandardResponse.format_validation_errors(serializer.errors)
    return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        device_token = serializer.validated_data.get('device_token')
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Update device token and last login
            if device_token:
                user.device_token = device_token
            user.last_login = timezone.now()
            user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': UserSerializer(user).data
            }
            
            response = StandardResponse.success(
                data=response_data,
                message='Login successful'
            )
            
            # Set tokens in HTTP-only cookies
            response.set_cookie(
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite='None',
                max_age=900
            )
            response.set_cookie(
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=True,
                samesite='None',
                max_age=604800
            )
            
            return response
        
        return StandardResponse.unauthorized(message='Invalid email or password')
    
    error_message = StandardResponse.format_validation_errors(serializer.errors)
    return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        # Clear device token
        user = request.user
        user.device_token = None
        user.save()
        
        # Blacklist refresh token if in cookies
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        response = StandardResponse.success(message='Logout successful')
        
        # Delete cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        
        return response
    except Exception as e:
        return StandardResponse.error(message='Logout failed', status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get current authenticated user"""
    serializer = UserSerializer(request.user)
    return StandardResponse.success(data=serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding_view(request):
    """Complete user onboarding"""
    user = request.user
    
    if user.is_onboarded:
        return StandardResponse.error(
            message='User already onboarded',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = OnboardingSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return StandardResponse.success(
            data={'user': UserSerializer(user).data},
            message='Onboarding completed successfully'
        )
    
    error_message = StandardResponse.format_validation_errors(serializer.errors)
    return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def onboarding_status_view(request):
    """Check onboarding status"""
    user = request.user
    return StandardResponse.success(data={
        'is_onboarded': user.is_onboarded,
        'email': user.email,
        'name': user.name or None
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Refresh access token using refresh token from cookie"""
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return StandardResponse.unauthorized(message='Refresh token not found')
    
    try:
        refresh = RefreshToken(refresh_token)
        
        response = StandardResponse.success(message='Token refreshed successfully')
        
        # Set new access token in cookie
        response.set_cookie(
            key='access_token',
            value=str(refresh.access_token),
            httponly=True,
            secure=True,
            samesite='None',
            max_age=900
        )
        
        return response
    except Exception as e:
        return StandardResponse.unauthorized(message='Invalid or expired refresh token')


class UserUpdateView(generics.UpdateAPIView):
    """Update user profile"""
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return StandardResponse.success(
                data={'user': UserSerializer(instance).data},
                message='Profile updated successfully'
            )
        
        error_message = StandardResponse.format_validation_errors(serializer.errors)
        return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """Change user password"""
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return StandardResponse.success(message='Password changed successfully')
    
    error_message = StandardResponse.format_validation_errors(serializer.errors)
    return StandardResponse.error(message=error_message, status_code=status.HTTP_400_BAD_REQUEST)