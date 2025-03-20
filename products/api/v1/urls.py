from uuid import UUID
from django.urls import path
from .views import (
  CreateProductView, ProductsView, ProductDetailsView, 
  UpdateProductView, DeleteProductView, ProductActivationView,
  GetAllProductsForAdmin,
)

user_urls = [
  path("", ProductsView.as_view(), name="get-products"),
  path("<uuid:product_id>/", ProductDetailsView.as_view(), name="product-details")
]

vendor_urls = [
  path("create/", CreateProductView.as_view(), name='create-product'),
  path("update/<uuid:product_id>/", UpdateProductView.as_view(), name="update-product"),
  path("delete/<uuid:product_id>/", DeleteProductView.as_view(), name="delete-product"),
]

admin_urls = [
  path("admin/", GetAllProductsForAdmin.as_view(), name="get-products-for-admin"),
  path("activation/<uuid:product_id>/", ProductActivationView.as_view(), name="product-activation")
]

urlpatterns = user_urls + vendor_urls + admin_urls