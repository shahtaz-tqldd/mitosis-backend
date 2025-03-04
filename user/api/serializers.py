from rest_framework import serializers
from ..models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True, required=True, style={'input_type':'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type':'password'})

    class Meta:
        model = CustomUser
        fields = [
            'email','password', 'password_confirm',
            'first_name','last_name', 'phone',
            'address_line_1', 'address_line_2', 'city', 'state_province', 'postal_code', 'country',
            'role', 'is_newsletter_subscribed'
        ]

        extra_kwargs = {
            'phone':{'required': False},
            'address_line_1':{'required': False},
            'address_line_2':{'required': False},
            'city':{'required': False},
            'state_province':{'required':False},
            'postal_code':{'required': False},
            'country':{'required': False}
        }

    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm":"Password do not match!"})
        
        try:
            validate_password(data['password'])

        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()

        return user

class GetUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"