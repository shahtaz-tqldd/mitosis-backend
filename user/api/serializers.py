from rest_framework import serializers
from ..models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from app.helpers.func import extra_kwargs_constructor


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = CustomUser
        fields = ["email", "password", "password_confirm", "first_name", "last_name"]

        extra_kwargs = extra_kwargs_constructor(
            "phone",
            "role",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "is_newsletter_subscribed",
        )

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Password do not match!"}
            )

        try:
            validate_password(data["password"])

        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        if data.get("role") == "ADMIN":
            raise serializers.ValidationError(
                {"forbidden": "ADMIN user not be created!"}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()

        return user


class GetUserListSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    is_vendor = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "fullname",
            "email",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "role",
            "profile_picture_url",
            "date_of_birth",
            "is_newsletter_subscribed",
            "is_vendor",
        ]

    def get_fullname(self, obj):
        return obj.get_full_name()

    def get_is_vendor(self, obj):
        return obj.is_vendor


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError({"error": "Invalid Credentials"})

        if not user.is_active:
            raise serializers.ValidationError({"error": "User is disabled"})

        refresh = RefreshToken.for_user(user)

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)


class UserDetailsSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "fullname",
            "email",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "role",
            "profile_picture_url",
            "date_of_birth",
            "is_newsletter_subscribed",
        ]

    def get_fullname(self, obj):
        return obj.get_full_name()


class UserDetailsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "profile_picture_url",
            "date_of_birth",
        ]


class UserDetailsForAdminSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    is_vendor = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "fullname",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "role",
            "profile_picture_url",
            "date_of_birth",
            "date_joined",
            "last_login",
            "is_newsletter_subscribed",
            "is_vendor",
            "is_active",
            "is_verified",
        ]

    def get_fullname(self, obj):
        return obj.get_full_name()

    def get_is_vendor(self, obj):
        return obj.is_vendor


class BaseUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ["fullname", "email", "phone"]

    def get_fullname(self, obj):
        return obj.get_full_name()
