from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')
    
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'password2', 'timezone']
        extra_kwargs = {
            'timezone': {'required': False}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            timezone=validated_data.get('timezone', 'UTC')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    device_token = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OnboardingSerializer(serializers.ModelSerializer):
    """Serializer for user onboarding"""
    
    class Meta:
        model = CustomUser
        fields = ['name', 'birthdate', 'gender']
        extra_kwargs = {
            'name': {'required': True},
            'birthdate': {'required': True},
            'gender': {'required': True}
        }
    
    def validate_birthdate(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Birthdate cannot be in the future.")
        return value
    
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.birthdate = validated_data.get('birthdate', instance.birthdate)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.is_onboarded = True
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'name', 'birthdate', 'gender', 
            'timezone', 'phone_number', 'is_onboarded', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'is_onboarded', 'date_joined', 'last_login']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = CustomUser
        fields = ['name', 'birthdate', 'gender', 'timezone', 'phone_number']
    
    def validate_birthdate(self, value):
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Birthdate cannot be in the future.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password')
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value