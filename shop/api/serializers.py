from rest_framework import serializers
from shop.models import Shop
from user.api.serializers import BaseUserSerializer

class CreateShopSerializer(serializers.ModelSerializer):
  class Meta:
    model = Shop
    exclude = ["user", "created_at", "updated_at"]

  def validate(self, data):
    user = self.context["request"].user

    if Shop.objects.filter(user=user).exists():
      raise serializers.ValidationError("You have already created a shop!")
    
    longitude = data.get("longitude")
    latitude = data.get("latitude")

    if (longitude is None) ^ (latitude is None):
      raise serializers.ValidationError("longitude and latitude must be provided together")
    
    return data
    

  def create(self, validated_data):
    user = self.context["request"].user
    return Shop.objects.create(user=user, **validated_data)
  

class ShopSerializer(serializers.ModelSerializer):
  class Meta:
    model = Shop
    exclude = ["user", "created_at", "updated_at"]


class ShopDetailsSerializer(serializers.ModelSerializer):
  user  = BaseUserSerializer()
  class Meta:
    model = Shop
    fields = "__all__"


class BaseShopSerializer(serializers.ModelSerializer):
  class Meta:
    model = Shop
    fields = ["name", "logo"]