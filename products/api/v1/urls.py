from django.urls import path
from .views import CreateProductView

user_urls = [
]

vendor_urls = [
  path('create/', CreateProductView.as_view(), name='create-product'),
]

admin_urls = [

]

urlpatterns = user_urls + vendor_urls + admin_urls