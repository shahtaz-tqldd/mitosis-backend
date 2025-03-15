from rest_framework import generics
from rest_framework.status import HTTP_201_CREATED
from ..serializers import CreateProductSerializer
from app.permission import IsAdminUser, IsVendorUser
from app.utils.response import APIResponse

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