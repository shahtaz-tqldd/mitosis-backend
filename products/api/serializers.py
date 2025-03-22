from rest_framework import serializers
from shop.api.serializers import BaseShopSerializer
from products.models import Product, ProductVariant, AttributeValue, Category, ProductImage
from app.helpers.func import extra_kwargs_constructor
from django.shortcuts import get_object_or_404
from shop.models import Shop
from products.helpers.validation import ProductValidationMixin


# CREATE PRODUCTS
class ProductImageSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductImage
    fields=["image"]
    extra_kwargs = extra_kwargs_constructor("alt_text")


class CreateProductVariantSerializer(serializers.ModelSerializer, ProductValidationMixin):
  attributes = serializers.PrimaryKeyRelatedField(queryset = AttributeValue.objects.all(), many=True)
  images = ProductImageSerializer(many=True)

  class Meta:
    fields = ["name", "attributes", "sku", "base_price", "stock", "images"]
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

  class Meta:
    model = Product
    fields = ["name", "description", "base_price", "stock", "sku", "status", "variants", "images"]
    extra_kwargs = extra_kwargs_constructor(
      "body_html",
      "tags",
      "discount_percents",
      "weight",
      "dimensions"
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

      product = Product.objects.create(created_by=created_by, shop=shop, **validated_data)
      
      # bulk create product image
      if images_data:
        images = [
          ProductImage(product=product, **image_data) for image_data in images_data
        ]

        ProductImage.objects.bulk_create(images)

      # bulk create variants and variant images
      if variants_data:
        variant_objects = []
        variant_images = []

        for variant_data in variants_data:
          variant_images_data = variant_data.pop("images", [])
          variant = ProductVariant(product=product, **variant_data)
          variant_objects.append(variant)

          for image_data in variant_images_data:
            variant_images.append((variant, image_data))

        
        # bulk create of product variants
        created_variants = ProductVariant.objects.bulk_create(variant_objects)

        if variant_images:
          variant_map = {i: variant for i, variant in enumerate(created_variants)}
          
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


# class CreatedProductDetailsSerializer(serializers.ModelSerializer):


# GET PRODUCTS
class ProductVariantSerializer(serializers.ModelSerializer):
  attributes = serializers.PrimaryKeyRelatedField(queryset = AttributeValue.objects.all(), many=True)
  class Meta:
    fields = ["name", "attributes", "sku", "base_price", "discount_percents", "stock"]

class BaseProductVariantSerializer(serializers.ModelSerializer):
  is_available = serializers.SerializerMethodField()
  class Meta:
    model = ProductVariant
    exclude = ["product", "is_active", "stock", "updated_at"]

  def get_is_available(self, obj):
    return obj.stock > 0 if obj.stock else False
  

class ProductSerializer(serializers.ModelSerializer):
  shop = BaseShopSerializer()
  category = serializers.StringRelatedField()
  is_available = serializers.SerializerMethodField()

  class Meta:
    model = Product
    fields = ["id", "name", "base_price", "discount_percents", "category", "shop", "is_available"]
  
  def get_is_available(self, obj):
    return obj.stock > 0 if obj.stock else False


class ProductDetailsSerializer(serializers.ModelSerializer):
  shop = BaseShopSerializer()
  category = serializers.StringRelatedField()
  variants = BaseProductVariantSerializer(many=True, read_only=True)
  is_available = serializers.SerializerMethodField()

  class Meta:
    model = Product
    exclude = ["created_by", "stock", "status", "updated_at"]
  
  def get_is_available(self, obj):
    return obj.stock > 0 if obj.stock else False
  



class UpdateProductDetailsSerializer(serializers.ModelSerializer):
  category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
  variants = ProductVariantSerializer(many=True, required=False)

  class Meta:
    model = Product
    fields = ["category", "variants"]

  def update(self, instance, validated_data):
    if 'category' in validated_data:
      instance.category = validated_data['category']

    instance.save()

    variants_data = validated_data.get('variants', [])
    existing_variants = {variant.id: variant for variant in instance.variants.all()}  # Get existing variants

    for variant_data in variants_data:
        variant_id = variant_data.get("id")

        if variant_id and variant_id in existing_variants:
            variant = existing_variants[variant_id]
            for key, value in variant_data.items():
                setattr(variant, key, value)
            variant.save()
        else:
            ProductVariant.objects.create(product=instance, **variant_data)

    return instance
  
  
class ProductListSerializerForAdmin(serializers.ModelSerializer):
  shop = BaseShopSerializer()
  category = serializers.StringRelatedField()
  is_available = serializers.SerializerMethodField()

  class Meta:
    model = Product
    fields = ["id", "name", "base_price", "discount_percents", "category", "shop", "status", "is_available"]
  
  def get_is_available(self, obj):
    return obj.stock > 0 if obj.stock else False