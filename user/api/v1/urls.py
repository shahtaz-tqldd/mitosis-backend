
from django.urls import path
from .views import CreateNewUserView, GetUserListView

user_urls =[
  path('register/', CreateNewUserView.as_view(), name="create-user"),
  
]

admin_urls = [
  path('admin/user-list/', GetUserListView.as_view(), name="user-list")
]


urlpatterns = user_urls + admin_urls