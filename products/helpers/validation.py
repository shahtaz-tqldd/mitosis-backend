from rest_framework import serializers
from app.utils import constants

class ProductValidationMixin:
  def validate_discount_percents(self, value):
    if value < 0 or value > 100:
      raise serializers.ValidationError("Discount percentage must be between 0.00 to 100.00!")
    
    return value
    
  def validate_stock(self, value):
    if value < 0:
      raise serializers.ValidationError("Stock cannot be negative!")

    return value
  
  def validate_images(self, value):
    if not value:
      raise serializers.ValidationError("You must provide at least one image for the product!")
    
    if len(value)>=constants.MAX_IMAGE_COUNT:
      raise serializers.ValidationError(f"You cannot upload more than {constants.MAX_IMAGE_COUNT} images for each product!")
    
    return value