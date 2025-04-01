from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend

from app.permission import IsAdminUser, IsVendorUser, IsProductOwner
from app.utils.response import APIResponse
from app.utils.pagination import CustomPagination

# models
from products.models import Product, ProductVariant
from shop.models import Shop

# serializers
from products.api.serializers import (
    CreateProductSerializer,
    ProductSerializer,
    ProductDetailsSerializer,
    UpdateProductDetailsSerializer,
    ProductListSerializerForAdminAndVendor,
    ProductDetailsSerializerForAdminAndVendor,
    CreateNewProductVariantsSerializer,
    ProductVariantSerializerForAdminAndVendor,
    UpdateProductVariantSerializer,
)


# USER VIEWS
class ProductsView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "base_price"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Product.objects.filter(status="published", is_restricted=False)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse.success(
            data=response.data, message="Product list retrieved!"
        )


class ProductDetailsView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductDetailsSerializer

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get("id")
        product = get_object_or_404(Product, id=product_id)
        serializer = self.get_serializer(product)
        return APIResponse.success(
            data=serializer.data, message="Product details retrieved!"
        )


# VENDOR VIEWS
class CreateProductView(generics.CreateAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = CreateProductSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.save()
        product_data = ProductDetailsSerializer(
            product, context=self.get_serializer_context()
        ).data

        return APIResponse.success(
            data=product_data,
            message="New Product Created Successfully!",
            status=HTTP_201_CREATED,
        )


class UpdateProductView(generics.UpdateAPIView):
    permission_classes = [IsVendorUser, IsProductOwner]
    serializer_class = UpdateProductDetailsSerializer
    queryset = Product.objects.all()
    lookup_field = "id"

    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        product = serializer.save()

        product_data = ProductDetailsSerializer(
            product, context=self.get_serializer_context()
        ).data

        return APIResponse.success(
            data=product_data, message="Product details updated!"
        )


class GetProductsForVendorView(generics.ListAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = ProductListSerializerForAdminAndVendor
    pagination_class = CustomPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "base_price"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        shop = Shop.objects.get(user=user)
        return Product.objects.filter(shop=shop)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return APIResponse.success(data=response.data, message="Product List for Shop")


class GetProductDetailsForVendorView(generics.RetrieveAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = ProductDetailsSerializerForAdminAndVendor

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get("id")
        product = get_object_or_404(Product, id=product_id)
        serializer = self.get_serializer(product)
        return APIResponse.success(
            data=serializer.data, message="Product details for shop user!"
        )


class DeleteProductView(generics.DestroyAPIView):
    permission_classes = [IsVendorUser]
    lookup_field = "id"

    def get_object(self):
        user = self.request.user
        shop = Shop.objects.get(user=user)

        product = get_object_or_404(Product, id=self.kwargs["id"], shop=shop)
        return product

    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        product.delete()

        return APIResponse.success(
            message="Product deleted successfully!", status=HTTP_204_NO_CONTENT
        )


class CreateProductVariants(generics.CreateAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = CreateNewProductVariantsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_variants = serializer.save()

        variants_data = ProductVariantSerializerForAdminAndVendor(
            created_variants, many=True, context=self.get_serializer_context()
        ).data

        return APIResponse.success(
            data=variants_data,
            message="New Product Variants created!",
            status=HTTP_201_CREATED,
        )


class UpdateProductVariant(generics.UpdateAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = UpdateProductVariantSerializer
    queryset = ProductVariant.objects.all()
    lookup_field = "id"
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return APIResponse.success(
            data=response.data,
            message="Product Variant updated!",
        )


class DeleteProductVariant(generics.DestroyAPIView):
    permission_classes = [IsVendorUser]
    queryset = ProductVariant.objects.all()
    lookup_field = "id"

    def get_object(self):
        user = self.request.user
        variant = super().get_object()
        product = variant.product

        shop = product.shop
        if shop.user != user:
            raise PermissionDenied(
                "You are not allowed to delete this product variant."
            )

        # Return the variant if the checks pass
        return variant

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return APIResponse.success(
            message="Product Variant deleted!", status=HTTP_204_NO_CONTENT
        )


# ADMIN VIEWS
class ProductRestrictView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        product_id = request.data.get("product_id")
        is_restricted = request.data.get("is_restrict")

        product = get_object_or_404(Product, id=product_id)
        product.is_restricted = is_restricted
        product.save()

        return APIResponse.success(
            # data = product,
            message=f"Product {"restricted" if is_restricted else "unrestricted"} successfully!"
        )


class GetAllProductsForAdminView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductListSerializerForAdminAndVendor
    queryset = Product.objects.all()

    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "base_price"]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "price"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        resposne = super().list(request, *args, **kwargs)
        return APIResponse.success(data=resposne.data, message="Product List for Admin")


class GetProductDetailsForAdminView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductDetailsSerializerForAdminAndVendor

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get("id")
        product = get_object_or_404(Product, id=product_id)
        serializer = self.get_serializer(product)
        return APIResponse.success(
            data=serializer.data, message="Product details for admin!"
        )
