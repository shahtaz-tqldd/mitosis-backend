from django.urls import path
from .views import (
    ProductsView,
    ProductDetailsView,
    GetProductsForVendorView,
    GetProductDetailsForVendorView,
    CreateProductView,
    UpdateProductView,
    DeleteProductView,
    CreateProductVariants,
    UpdateProductVariant,
    DeleteProductVariant,
    GetAllProductsForAdminView,
    GetProductDetailsForAdminView,
    ProductRestrictView,
)

user_urls = [
    path("", ProductsView.as_view(), name="get-products"),
    path("<uuid:id>/", ProductDetailsView.as_view(), name="product-details"),
]

vendor_urls = [
    path("shop/", GetProductsForVendorView.as_view(), name="get-products-for-vendor"),
    path(
        "shop/<uuid:id>/",
        GetProductDetailsForVendorView.as_view(),
        name="get-product-details-for-vendor",
    ),
    path("create/", CreateProductView.as_view(), name="create-product"),
    path("update/<uuid:id>/", UpdateProductView.as_view(), name="update-product"),
    path("delete/<uuid:id>/", DeleteProductView.as_view(), name="delete-product"),
    path(
        "variants/create/<uuid:product_id>/",
        CreateProductVariants.as_view(),
        name="create-product-variant",
    ),
    path(
        "variants/update/<uuid:id>/",
        UpdateProductVariant.as_view(),
        name="update-product-variant",
    ),
    path(
        "variants/delete/<uuid:id>/",
        DeleteProductVariant.as_view(),
        name="delete-product-variant",
    ),
]

admin_urls = [
    path("admin/", GetAllProductsForAdminView.as_view(), name="get-products-for-admin"),
    path(
        "admin/<uuid:id>/",
        GetProductDetailsForAdminView.as_view(),
        name="get-product-details-for-admin",
    ),
    path("admin/restrict/", ProductRestrictView.as_view(), name="restrict-product"),
]

urlpatterns = user_urls + vendor_urls + admin_urls
