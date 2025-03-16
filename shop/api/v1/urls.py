from django.urls import path
from .views import (
  CreateShopView, UpdateShopView, ShopDetailsView, 
  ShopListView, ShopActivationView, ShopDetailsForAdminView
  )


vendor_urls = [
  path("create/", CreateShopView.as_view(), name="create-shop"),
  path("update/", UpdateShopView.as_view(), name="update-shop"),
  path("shop-details/", ShopDetailsView.as_view(), name="shop-details")
]

admin_urls = [
  path("admin/shop-list/", ShopListView.as_view(), name="shop-list"),
  path("admin/activation/<int:shop_id>/", ShopActivationView.as_view(), name="shop-activation"),
  path("admin/shop-details/<int:shop_id>/", ShopDetailsForAdminView.as_view(), name="shop-details-for-admin")
]

urlpatterns = vendor_urls + admin_urls