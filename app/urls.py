
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('user.api.v1.urls')),
    path('api/v1/products/', include('products.api.v1.urls')),
]
