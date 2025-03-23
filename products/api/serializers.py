from django.shortcuts import get_object_or_404
from rest_framework import serializers

from app.helpers.func import extra_kwargs_constructor

from shop.api.serializers import BaseShopSerializer
from products.helpers.validation import ProductValidationMixin

# models
from shop.models import Shop
from products.models import (
    Product,
    ProductVariant,
    AttributeValue,
    Category,
    ProductImage,
)


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image"]
        extra_kwargs = extra_kwargs_constructor("alt_text")


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = ["attribute_name", "value"]


class CategotySerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["id", "name"]
        extra_kwargs = extra_kwargs_constructor("parent")


# PRODUCT VARIANT


class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "name",
            "attributes",
            "base_price",
            "discount_percents",
            "images",
            "is_available",
        ]

    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False


# CREATE PRODUCTS
class CreateProductVariantSerializer(
    serializers.ModelSerializer, ProductValidationMixin
):
    attributes = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all(), many=True
    )
    images = ProductImageSerializer(many=True)

    class Meta:
        model = ProductVariant
        fields = ["name", "attributes", "base_price", "stock", "images"]
        extra_kwargs = extra_kwargs_constructor("discount_percents")

    def validate_discount_percents(self, value):
        return super().validate_discount_percents(value)

    def validate_stock(self, value):
        return super().validate_stock(value)

    def validate_images(self, value):
        return super().validate_images(value)


class CreateProductSerializer(serializers.ModelSerializer, ProductValidationMixin):
    variants = CreateProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "base_price",
            "category",
            "stock",
            "sku",
            "status",
            "variants",
            "images",
        ]
        extra_kwargs = extra_kwargs_constructor(
            "body_html", "tags", "discount_percents", "weight", "dimensions"
        )

    def validate_discount_percents(self, value):
        return super().validate_discount_percents(value)

    def validate_stock(self, value):
        return super().validate_stock(value)

    def validate_images(self, value):
        return super().validate_images(value)

    def create(self, validated_data):
        request = self.context.get("request")
        if request:
            created_by = request.user
            shop = get_object_or_404(Shop, user=created_by)

            variants_data = validated_data.pop("variants", [])
            images_data = validated_data.pop("images", [])

            product = Product.objects.create(
                created_by=created_by, shop=shop, **validated_data
            )

            # bulk create product image
            if images_data:
                images = [
                    ProductImage(product=product, **image_data)
                    for image_data in images_data
                ]
                ProductImage.objects.bulk_create(images)

            # bulk create variants and variant images
            if variants_data:
                variant_objects = []
                variant_images = []
                variant_attributes = []

                for variant_data in variants_data:
                    variant_images_data = variant_data.pop("images", [])
                    attributes_data = variant_data.pop("attributes", [])
                    variant = ProductVariant(product=product, **variant_data)
                    variant_objects.append(variant)
                    variant_attributes.append(attributes_data)

                    for image_data in variant_images_data:
                        variant_images.append((variant, image_data))

                # bulk create of product variants
                created_variants = ProductVariant.objects.bulk_create(variant_objects)

                # Set attributes for each variant
                for i, variant in enumerate(created_variants):
                    variant.attributes.set(variant_attributes[i])

                if variant_images:
                    variant_map = {
                        i: variant for i, variant in enumerate(created_variants)
                    }

                    variant_image_objects = []

                    for i, (temp_variant, img_data) in enumerate(variant_images):
                        variant_index = variant_objects.index(temp_variant)
                        actual_variant = variant_map[variant_index]

                        variant_image_objects.append(
                            ProductImage(variant=actual_variant, **img_data)
                        )

                    # bulk create of variant images
                    if variant_image_objects:
                        ProductImage.objects.bulk_create(variant_image_objects)

            return product


# UPDATE PRODUCTS


class UpdateProductDetailsSerializer(
    serializers.ModelSerializer, ProductValidationMixin
):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False
    )
    variants = CreateProductVariantSerializer(many=True, required=False)
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "body_html",
            "tags",
            "base_price",
            "discount_percents",
            "stock",
            "sku",
            "status",
            "weight",
            "dimensions",
            "category",
            "variants",
            "images",
        ]

    def validate_discount_percents(self, value):
        return super().validate_discount_percents(value)

    def validate_stock(self, value):
        return super().validate_stock(value)

    def validate_images(self, value):
        return super().validate_images(value)

    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants")
        images_data = validated_data.pop("images")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if variants_data is not None:
            self._handle_variants_update(instance, variants_data)

        if images_data is not None:
            self._handle_images_update(instance, images_data)

        return instance

    def _handle_images_update(self, product, images_data):
        existing_image_ids = set(product.images.values_list("id", flat=True))
        update_image_ids = set()

        for image_data in images_data:
            image_id = image_data.get("id", None)

            if image_id:
                if image_id in existing_image_ids:
                    update_image_ids.add(image_id)
                    image = ProductImage.objects.get(id=image_id)

                    for attr, value in image_data.items():
                        if attr != "id":
                            setattr(image, attr, value)

                    image.save()

            else:
                ProductImage.objects.create(product=product, **image_data)

        images_to_delete = existing_image_ids - update_image_ids

        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete).delete()


# GET PRODUCTS
# 1. Get minilam product details for product card
class ProductSerializer(serializers.ModelSerializer):
    shop = BaseShopSerializer()
    category = serializers.StringRelatedField()
    is_available = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "images",
            "base_price",
            "discount_percents",
            "category",
            "shop",
            "is_available",
        ]

    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False


# 2. Get all the necessary details for product
class ProductDetailsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()  # Ensure ID is first if needed
    name = serializers.CharField()
    description = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percents = serializers.DecimalField(max_digits=5, decimal_places=2)
    category = serializers.StringRelatedField()
    is_available = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True)
    shop = BaseShopSerializer()
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "base_price",
            "discount_percents",
            "category",
            "is_available",
            "images",
            "shop",
            "variants",
        ]

    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False


# 3. get product list for admin
class ProductListSerializerForAdmin(serializers.ModelSerializer):
    shop = BaseShopSerializer()
    category = serializers.StringRelatedField()
    is_available = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "images",
            "base_price",
            "discount_percents",
            "category",
            "shop",
            "status",
            "is_available",
        ]

    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False
