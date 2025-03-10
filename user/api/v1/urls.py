from django.urls import path
from .views import (
  CreateNewUserView, LoginView, RefreshTokenView, UserDetailsView, 
  ForgetPasswordView, ResetPasswordView, GetUserListView,
  )

user_urls =[
  path('register/', CreateNewUserView.as_view(), name="create-user"),
  path('login/', LoginView.as_view(), name="login"),
  path('token-refresh/', RefreshTokenView.as_view(), name="token-refresh"),
  path('user-details/', UserDetailsView.as_view(), name="user-details"),
  path('forget-password/', ForgetPasswordView.as_view(), name="forget-password"),
  path('reset-password/', ResetPasswordView.as_view(), name="reset-password")
]

admin_urls = [
  path('admin/user-list/', GetUserListView.as_view(), name="user-list")
]


urlpatterns = user_urls + admin_urls