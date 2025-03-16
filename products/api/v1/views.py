from rest_framework import generics, permissions
from rest_framework.status import HTTP_201_CREATED

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from app.permission import IsAdminUser, IsVendorUser
from app.utils.response import APIResponse
from app.utils.pagination import CustomPagination

from products.api.serializers import (
  CreateProductSerializer, ProductSerializer
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
  def get(self, request, *args, **kwargs):
    return APIResponse.success(message="Product details retrieved!")



# VENDOR VIEWS
class CreateProductView(generics.CreateAPIView):
  serializer_class = CreateProductSerializer
  permission_classes = [IsVendorUser]

  def post(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    product = serializer.save()
    product_data = CreateProductSerializer(product).data

    return APIResponse.success(
      data = product_data,
      message = "New Product Created Successfully!",
      status = HTTP_201_CREATED
    )


class UpdateProductView(generics.UpdateAPIView):
  permission_classes = [IsVendorUser]

  def update(self, request, *args, **kwargs):
    return APIResponse.success(message="Product details updated!")
  
class DeleteProductView(generics.DestroyAPIView):
  permission_classes = [IsVendorUser]

  def destroy(self, request, *args, **kwargs):
    return APIResponse.success(message="Product deleted successfully!")

# ADMIN VIEWS


class ProductActivationView(generics.UpdateAPIView):

  def update(self, request, *args, **kwargs):
    return APIResponse.success(message = f"Product is activated successfully")