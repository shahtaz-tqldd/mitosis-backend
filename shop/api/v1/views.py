from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from app.utils.response import APIResponse
from app.permission import IsVendorUser, IsAdminUser

from shop.api.serializers import (
    CreateShopSerializer,
    ShopSerializer,
    ShopDetailsSerializer,
)
from shop.models import Shop


class CreateShopView(generics.CreateAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = CreateShopSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.save()
        product_data = CreateShopSerializer(product).data

        return APIResponse.success(
            data=product_data,
            message="Shop created successfully!",
            status=HTTP_201_CREATED,
        )


class UpdateShopView(generics.UpdateAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = ShopSerializer

    http_method_names = ["patch"]

    def get_shop(self):
        return get_object_or_404(Shop, user=self.request.user)

    def update(self, request, *args, **kwargs):
        shop = self.get_shop()
        serializer = self.get_serializer(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return APIResponse.success(
            data=serializer.data,
            message="Shop updated successfully!",
            status=HTTP_200_OK,
        )


class ShopDetailsView(generics.RetrieveAPIView):
    permission_classes = [IsVendorUser]
    serializer_class = ShopSerializer

    def get_shop(self):
        return get_object_or_404(Shop, user=self.request.user)

    def get(self, request, *args, **kwargs):
        shop = self.get_shop()
        serializer = self.get_serializer(shop)

        return APIResponse.success(
            data=serializer.data,
            message="Shop details retrieved!",
        )


# Admin View
class ShopActivationView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        shop_id = kwargs.get("shop_id")
        is_active = request.data.get("is_active")

        if shop_id is None:
            return APIResponse.error(message="shop id is required in the params")

        if is_active is None:
            return APIResponse.error(
                message="`is_active` field is required in the body"
            )

        shop = get_object_or_404(Shop, id=shop_id)

        shop.is_active = is_active
        shop.save(update_fields=["is_active"])

        return APIResponse.success(
            message=f"{shop.name} Shop is {'activated' if is_active else 'deactivated'} successfully!"
        )


class ShopListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Shop.objects.all()
    serializer_class = ShopDetailsSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return APIResponse.success(
            data=serializer.data, message="Shop List retrieved!", status=HTTP_200_OK
        )


class ShopDetailsForAdminView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ShopDetailsSerializer
    queryset = Shop.objects.all()

    def get_shop(self):
        shop_id = self.kwargs.get("shop_id")
        return get_object_or_404(Shop, id=shop_id)

    def get(self, request, *args, **kwargs):
        shop = self.get_shop()
        serializer = self.get_serializer(shop)

        return APIResponse.success(
            data=serializer.data, message="Shop details retrived"
        )
