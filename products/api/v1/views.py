from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions
from rest_framework.status import HTTP_201_CREATED

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from app.permission import IsAdminUser, IsVendorUser
from app.utils.response import APIResponse
from app.utils.pagination import CustomPagination

from products.api.serializers import (
  CreateProductSerializer, ProductSerializer, ProductDetailsSerializer, 
  UpdateProductDetailsSerializer, ProductListSerializerForAdmin
)
from products.models import Product


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
    return Product.objects.filter(status="published")

  def list(self, request, *args, **kwargs):
    response = super().list(request, *args, **kwargs)
    return APIResponse.success(data= response.data, message="Product list retrieved!")
  

class ProductDetailsView(generics.GenericAPIView):
  permission_classes = [permissions.AllowAny]
  serializer_class = ProductDetailsSerializer
  
  def get(self, request, *args, **kwargs):
    product_id  = self.kwargs.get("product_id")
    product = get_object_or_404(Product, id = product_id)
    serializer  = self.get_serializer(product)
    return APIResponse.success(data=serializer.data, message="Product details retrieved!")


# VENDOR VIEWS
class CreateProductView(generics.CreateAPIView):
  permission_classes = [IsVendorUser]
  serializer_class = CreateProductSerializer

  def post(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product = serializer.save()
    product_data = ProductDetailsSerializer(product, context=self.get_serializer_context()).data

    return APIResponse.success(
      data = product_data,
      message = "New Product Created Successfully!",
      status = HTTP_201_CREATED
    )


class UpdateProductView(generics.UpdateAPIView):
  permission_classes = [IsVendorUser]
  serializer_class = UpdateProductDetailsSerializer

  http_method_names = ["patch"]

  def get_queryset(self):
    user = self.request.user
    return Product.objects.filter(shop__owner=user)

  def update(self, request, *args, **kwargs):
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)

    serializer.save()

    return APIResponse.success(data=serializer.data, message="Product details updated!")
  
class DeleteProductView(generics.DestroyAPIView):
  permission_classes = [IsVendorUser]

  def destroy(self, request, *args, **kwargs):
    return APIResponse.success(message="Product deleted successfully!")



# ADMIN VIEWS

class ProductActivationView(generics.UpdateAPIView):
  def update(self, request, *args, **kwargs):
    return APIResponse.success(message = f"Product is activated successfully")
  

class GetAllProductsForAdmin(generics.ListAPIView):
  permission_classes = [IsAdminUser]
  serializer_class = ProductListSerializerForAdmin
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

