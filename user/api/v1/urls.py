from django.urls import path
from .views import (
    CreateNewUserView,
    LoginView,
    RefreshTokenView,
    UserDetailsView,
    UserDetailsUpdateView,
    ForgetPasswordView,
    ResetPasswordView,
    GetUserListView,
    UserDetailsForAdminView,
    UserActivationView,
)

user_urls = [
    path("register/", CreateNewUserView.as_view(), name="create-user"),
    path("login/", LoginView.as_view(), name="login"),
    path("token-refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("user-details/", UserDetailsView.as_view(), name="user-details"),
    path("user-details/update/", UserDetailsUpdateView.as_view(), name="update-user"),
    path("forget-password/", ForgetPasswordView.as_view(), name="forget-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]

admin_urls = [
    path("admin/user-list/", GetUserListView.as_view(), name="user-list"),
    path("admin/user-details/", UserDetailsForAdminView.as_view(), name="user-details"),
    path(
        "admin/user-activation/", UserActivationView.as_view(), name="user-activation"
    ),
]


urlpatterns = user_urls + admin_urls
