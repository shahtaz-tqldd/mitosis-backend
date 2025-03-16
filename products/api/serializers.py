from rest_framework import serializers
from shop.api.serializers import BaseShopSerializer
from products.models import Product, ProductVariant

class CreateProductSerializer(serializers.ModelSerializer):
  name = serializers.CharField(max_length=200)

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
  variants = BaseProductVariantSerializer(many=True, read_only=True)
  is_available = serializers.SerializerMethodField()

  class Meta:
    model = Product
    exclude = ["created_by", "stock", "status", "updated_at"]
  
  def get_is_available(self, obj):
    return obj.stock > 0 if obj.stock else False