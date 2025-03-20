from rest_framework import serializers
from shop.api.serializers import BaseShopSerializer
from products.models import Product, ProductVariant, AttributeValue, Category
from app.helpers.func import extra_kwargs_constructor
from django.shortcuts import get_object_or_404
from shop.models import Shop

class CreateProductSerializer(serializers.ModelSerializer):
  class Meta:
    model = Product
    fields = ["name", "description", "base_price", "stock", "sku", "status"]
    extra_kwargs = extra_kwargs_constructor(
      "body_html",
      "tags",
      "discount_percents",
      "weight",
      "dimensions"
    )
  
  def validate_discount_percents(self, value):
    if value < 0 or value > 100:
      raise serializers.ValidationError("Discount percentage must be between 0.00 and 100.00!")
    
    return value
    
  def validate_stock(self, value):
    if value < 0:
      raise serializers.ValidationError("Stock cannot be negative!")

    return value

  def create(self, validated_data):
    request = self.context.get("request")
    if request:
      created_by = request.user
      shop = get_object_or_404(Shop, user=created_by)
      product = Product.objects.create(created_by=created_by, shop=shop, **validated_data)
      return product


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
  

class ProductVariantSerializer(serializers.ModelSerializer):
  attributes = serializers.PrimaryKeyRelatedField(queryset = AttributeValue.objects.all(), many=True)
  class Meta:
    fields = ["id", "name", "attributes", "sku", "base_price", "discount_percents", "stock"]



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