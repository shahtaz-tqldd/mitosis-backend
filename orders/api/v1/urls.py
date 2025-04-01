from django.urls import path
from .views import (
    GetMyOrdersView, CancelOrderView,
    GetVendorOrdersView, UpdateOrderStatusView,
    GetAllOrdersForAdminView
)

user_urls = [
    path('my-orders/', GetMyOrdersView.as_view(), name="get-my-orders"),
    path('cancel-orders/<uuid:id>/', CancelOrderView.as_view(), name="cancel-my-orders"),
]

vendor_urls = [
    path('shop-orders/', GetVendorOrdersView.as_view(), name="get-vendor-orders"),
    path('update/<uuid:id>/', UpdateOrderStatusView.as_view(), name="update-order-status"),
]

admin_urls = [
    path("admin/", GetAllOrdersForAdminView.as_view(), name="get-all-orders-for-admin"),
]

urlpatterns = user_urls + vendor_urls + admin_urls
