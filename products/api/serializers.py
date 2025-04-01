from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.db import transaction

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


class UpdateProductImageSerializer(ProductImageSerializer):
    class Meta(ProductImageSerializer.Meta):
        fields = ["id", "image", "alt_text"]


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = ["attribute_name", "value"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
        extra_kwargs = extra_kwargs_constructor("parent")


# Base ProductVariant serializer with common fields
class BaseProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True)
    
    class Meta:
        model = ProductVariant
        abstract = True


# PRODUCT VARIANT - For standard users
class ProductVariantSerializer(BaseProductVariantSerializer):
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


# For admin and vendors - extend the base class
class ProductVariantSerializerForAdminAndVendor(BaseProductVariantSerializer):
    class Meta:
        model = ProductVariant
        exclude = ["product"]


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


class CreateNewProductVariantsSerializer(serializers.Serializer):
    variants = serializers.ListField(child=CreateProductVariantSerializer())

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is required.")

        created_by = request.user
        product_id = self.context["view"].kwargs["product_id"]
        shop = get_object_or_404(Shop, user=created_by)

        product = get_object_or_404(Product, shop=shop, id=product_id)

        # Extract variants from payload
        variants_data = validated_data.get("variants", [])
        if not variants_data:
            raise serializers.ValidationError("At least one variant is required.")

        # Prepare bulk creation lists
        variant_objects = []
        variant_attributes = []
        variant_images_data = []

        for variant_data in variants_data:
            images_data = variant_data.pop("images", [])  # Extract images
            attributes_data = variant_data.pop("attributes", [])  # Extract attributes

            variant = ProductVariant(product=product, **variant_data)
            variant_objects.append(variant)
            variant_attributes.append(attributes_data)
            variant_images_data.append(images_data)

        # Bulk create variants
        created_variants = ProductVariant.objects.bulk_create(variant_objects)

        # Assign attributes to each variant
        for i, variant in enumerate(created_variants):
            variant.attributes.set(variant_attributes[i])

        # Bulk create images for each variant
        variant_image_objects = []
        for i, variant in enumerate(created_variants):
            for img_data in variant_images_data[i]:
                variant_image_objects.append(ProductImage(variant=variant, **img_data))

        # Bulk create images
        if variant_image_objects:
            ProductImage.objects.bulk_create(variant_image_objects)

        return created_variants


class UpdateProductVariantSerializer(serializers.ModelSerializer):
    attributes = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all(), many=True, required=False
    )
    images = UpdateProductImageSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = ["name", "attributes", "base_price", "discount_percents", "stock", "images"]

    @transaction.atomic
    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", None)
        attributes_data = validated_data.pop("attributes", None)

        # Update standard fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update attributes if provided
        if attributes_data is not None:
            instance.attributes.set(attributes_data)

        # Update images (optional: remove old ones)
        if images_data is not None:
            # Process images more efficiently
            self._handle_images_update(instance, images_data)

        return instance
    
    def _handle_images_update(self, variant, images_data):
        existing_image_ids = set(variant.images.values_list("id", flat=True))
        updated_image_ids = set()
        images_to_update = []
        images_to_create = []

        for image_data in images_data:
            image_id = image_data.get("id", None)

            if image_id and image_id in existing_image_ids:
                updated_image_ids.add(image_id)
                image = ProductImage.objects.get(id=image_id)
                
                for attr, value in image_data.items():
                    if attr != "id":
                        setattr(image, attr, value)
                
                images_to_update.append(image)
            elif not image_id:
                images_to_create.append(ProductImage(variant=variant, **image_data))

        # Bulk update
        if images_to_update:
            ProductImage.objects.bulk_update(images_to_update, ["image", "alt_text"])
            
        # Bulk create
        if images_to_create:
            ProductImage.objects.bulk_create(images_to_create)
            
        # Delete unused images
        images_to_delete = existing_image_ids - updated_image_ids
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete).delete()


# CREATE PRODUCTS
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

    @transaction.atomic
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


# Base Product serializer
class BaseProductSerializer(serializers.ModelSerializer):
    shop = BaseShopSerializer()
    category = serializers.StringRelatedField()
    is_available = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True)
    
    class Meta:
        model = Product
        abstract = True
        
    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False


# UPDATE PRODUCTS
class UpdateProductDetailsSerializer(
    serializers.ModelSerializer, ProductValidationMixin
):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False
    )
    variants = CreateProductVariantSerializer(many=True, required=False)
    images = UpdateProductImageSerializer(many=True, required=False)

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

    @transaction.atomic
    def update(self, instance, validated_data):
        variants_data = validated_data.pop("variants", None)
        images_data = validated_data.pop("images", None)

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
        images_to_update = []
        images_to_create = []

        for image_data in images_data:
            image_id = image_data.get("id", None)

            if image_id and image_id in existing_image_ids:
                update_image_ids.add(image_id)
                image = ProductImage.objects.get(id=image_id)
                
                for attr, value in image_data.items():
                    if attr != "id":
                        setattr(image, attr, value)
                
                images_to_update.append(image)
            elif not image_id:
                images_to_create.append(ProductImage(product=product, **image_data))

        # Bulk operations
        if images_to_update:
            ProductImage.objects.bulk_update(images_to_update, ["image", "alt_text"])
        
        if images_to_create:
            ProductImage.objects.bulk_create(images_to_create)

        # Delete images not in the update
        images_to_delete = existing_image_ids - update_image_ids
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete).delete()

    def _handle_variants_update(self, product, variants_data):
        existing_variant_ids = set(product.variants.values_list("id", flat=True))
        updated_variant_ids = set()
        variants_to_update = []
        variants_to_create = []
        variant_images_mapping = {}
        variant_attributes_mapping = {}

        for variant_data in variants_data:
            variant_id = variant_data.get("id", None)
            variant_images = variant_data.pop("images", None)
            attributes_data = variant_data.pop("attributes", None)

            if variant_id and variant_id in existing_variant_ids:
                # Update existing variant
                updated_variant_ids.add(variant_id)
                variant = ProductVariant.objects.get(id=variant_id)

                for attr, value in variant_data.items():
                    if attr != "id":
                        setattr(variant, attr, value)
                
                variants_to_update.append(variant)
                
                # Store related data for bulk operations
                if attributes_data is not None:
                    variant_attributes_mapping[variant.id] = attributes_data
                
                if variant_images is not None:
                    variant_images_mapping[variant.id] = variant_images
            else:
                # Create new variant
                new_variant = ProductVariant(product=product, **variant_data)
                variants_to_create.append(new_variant)
                
                # Store temporary mapping for bulk creation later
                if attributes_data:
                    # Use a temporary key since we don't have an ID yet
                    variant_attributes_mapping[id(new_variant)] = attributes_data
                
                if variant_images:
                    variant_images_mapping[id(new_variant)] = variant_images

        # Bulk update existing variants
        if variants_to_update:
            ProductVariant.objects.bulk_update(
                variants_to_update, 
                ["name", "base_price", "discount_percents", "stock"]
            )
            
            # Process attributes and images for existing variants
            for variant in variants_to_update:
                if variant.id in variant_attributes_mapping:
                    variant.attributes.set(variant_attributes_mapping[variant.id])
                
                if variant.id in variant_images_mapping:
                    self._handle_variant_images_update(variant, variant_images_mapping[variant.id])

        # Bulk create new variants
        if variants_to_create:
            created_variants = ProductVariant.objects.bulk_create(variants_to_create)
            
            # Process attributes and images for new variants
            for i, variant in enumerate(variants_to_create):
                new_variant = created_variants[i]
                
                # Handle attributes
                temp_id = id(variant)
                if temp_id in variant_attributes_mapping:
                    new_variant.attributes.set(variant_attributes_mapping[temp_id])
                
                # Handle images
                if temp_id in variant_images_mapping:
                    images_to_create = []
                    for image_data in variant_images_mapping[temp_id]:
                        images_to_create.append(ProductImage(variant=new_variant, **image_data))
                    
                    if images_to_create:
                        ProductImage.objects.bulk_create(images_to_create)

        # Delete variants not in the update
        variants_to_delete = existing_variant_ids - updated_variant_ids
        if variants_to_delete:
            ProductVariant.objects.filter(id__in=variants_to_delete).delete()

    def _handle_variant_images_update(self, variant, images_data):
        existing_image_ids = set(variant.images.values_list("id", flat=True))
        updated_image_ids = set()
        images_to_update = []
        images_to_create = []

        for image_data in images_data:
            image_id = image_data.get("id", None)

            if image_id and image_id in existing_image_ids:
                updated_image_ids.add(image_id)
                image = ProductImage.objects.get(id=image_id)
                for attr, value in image_data.items():
                    if attr != "id":
                        setattr(image, attr, value)
                images_to_update.append(image)
            elif not image_id:
                images_to_create.append(ProductImage(variant=variant, **image_data))

        # Bulk operations
        if images_to_update:
            ProductImage.objects.bulk_update(images_to_update, ["image", "alt_text"])
        
        if images_to_create:
            ProductImage.objects.bulk_create(images_to_create)

        # Delete images not in the update
        images_to_delete = existing_image_ids - updated_image_ids
        if images_to_delete:
            ProductImage.objects.filter(id__in=images_to_delete).delete()


# GET PRODUCTS
# 1. Get product list for user
class ProductSerializer(BaseProductSerializer):
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


# 2. Get product details for user
class ProductDetailsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    sku = serializers.CharField()
    description = serializers.CharField()
    body_html = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percents = serializers.DecimalField(max_digits=5, decimal_places=2)
    category = serializers.StringRelatedField()
    tags = serializers.ListField(child=serializers.CharField())
    is_available = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True)
    shop = BaseShopSerializer()
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "body_html",
            "base_price",
            "discount_percents",
            "category",
            "tags",
            "is_available",
            "images",
            "shop",
            "variants",
        ]

    def get_is_available(self, obj):
        return obj.stock > 0 if obj.stock else False


# 3. get product list for admin and vendor
class ProductListSerializerForAdminAndVendor(BaseProductSerializer):
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


# 4. get product details for admin and vendor
class ProductDetailsSerializerForAdminAndVendor(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    sku = serializers.CharField()
    description = serializers.CharField()
    body_html = serializers.CharField()
    base_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percents = serializers.DecimalField(max_digits=5, decimal_places=2)
    category = serializers.StringRelatedField()
    tags = serializers.ListField(child=serializers.CharField())
    stock = serializers.IntegerField(default=0)
    is_restricted = serializers.BooleanField()
    images = ProductImageSerializer(many=True)
    shop = BaseShopSerializer()
    variants = ProductVariantSerializerForAdminAndVendor(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "body_html",
            "base_price",
            "discount_percents",
            "category",
            "tags",
            "stock",
            "is_restricted",
            "images",
            "shop",
            "variants",
        ]