from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Address


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password', 'confirm_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        """Validate passwords match and meet requirements."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        
        if len(data['password']) < 8:
            raise serializers.ValidationError({'password': 'Password must be at least 8 characters'})
        
        return data
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Validate email and password."""
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password')
        
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating user profile."""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'date_joined')
        read_only_fields = ('id', 'email', 'date_joined')


class AddressSerializer(serializers.ModelSerializer):
    """Serializer for user addresses."""
    
    class Meta:
        model = Address
        fields = ('id', 'street', 'city', 'state', 'country', 'is_default', 'created_at')
        read_only_fields = ('id', 'created_at')
