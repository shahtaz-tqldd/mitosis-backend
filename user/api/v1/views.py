import random
from django.core.mail import send_mail
from rest_framework import generics, permissions
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from app.permission import IsAdminUser
from app.utils.response import APIResponse

from user.models import CustomUser, PasswordResetOTP
from user.api.serializers import (
    CreateUserSerializer, GetUserListSerializer, LoginSerializer, 
    ForgetPasswordSerializer, ResetPasswordSerializer
)

from django.contrib.auth import get_user_model

User = get_user_model()

class CreateNewUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_data = CreateUserSerializer(user).data

        return APIResponse.success(
            data= user_data,
            message= "New User Created!",
            status= HTTP_201_CREATED
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return APIResponse.success(
            data=serializer.validated_data,
            message="User logged in!",
            status= HTTP_200_OK
        )
    

class RefreshTokenView(TokenRefreshView):
    def post(self,request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token_data = {
            "access_token": response.data.get("access"),
            "refresh_token": response.data.get("refresh"),
        }
        return APIResponse.success(
            data= token_data,
            status= HTTP_200_OK,
            message="Token refreshed success!"
        )


class ForgetPasswordView(generics.GenericAPIView):
    serializer_class = ForgetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer  = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return APIResponse.error(message="User does not exist with this email", status=HTTP_404_NOT_FOUND )
        
        otp = str(random.randint(1000, 9999))

        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject="Your password reset OTP",
            message = f"Hey {user.first_name}, Your otp for password reset is {otp} and validity is 10 minutes",
            from_email = "",
            recipient_list = [email],
            fail_silently = False
        )

        return APIResponse.success(message="An OTP has sent to your email!")
    

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serialzier = self.get_serializer(data=request.data)
        serialzier.is_valid(raise_exception=True)

        email = serialzier.validated_data['email']
        otp = serialzier.validated_data['otp']
        new_password = serialzier.validated_data['new_password']
        confirm_password = serialzier.validated_data['confirm_password']

        if new_password != confirm_password:
            return APIResponse.error(message="Password did not match!", status=HTTP_409_CONFLICT)
        
        user = User.objects.filter(email=email).first()
        if not user:
            return APIResponse.error(message="User does not exist with this email", status=HTTP_404_NOT_FOUND)
        
        otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp).last()

        if not otp_entry or not otp_entry.is_valid():
            return APIResponse.error(message="Invalid or expired OTP")
        
        user.set_password(new_password)
        user.save()

        otp_entry.delete()

        return APIResponse.success(message="Password reset successfully")
        
        
class GetUserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = GetUserListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return APIResponse.success(
            data= serializer.data,
            message="User data fetched!",
            status=HTTP_200_OK,
        )

