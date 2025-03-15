from django.db import models
from user.models import CustomUser
from django.core.exceptions import ValidationError

# Shop
class Shop(models.Model):
  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
  name = models.CharField(max_length=80)
  description = models.TextField()

  logo = models.ImageField(upload_to="static/images/shop/", blank=True, null=True)
  banner = models.ImageField(upload_to="static/images/shop/", blank=True, null=True)

  address = models.CharField(max_length=255, blank=True, null=True)
  city = models.CharField(max_length=80, blank=True, null=True)
  state_province = models.CharField(max_length=100, blank=True, null=True)
  country = models.CharField(max_length=100, blank=True, null=True)
  postal_code = models.CharField(max_length=10, blank=True,null=True)
  longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
  latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

  phone = models.CharField(max_length=20, blank=True, null=True)
  email = models.EmailField(blank=True, null=True)
  social_media_link_1 = models.CharField(max_length=80, blank=True, null=True)
  social_media_link_2 = models.CharField(max_length=80, blank=True, null=True)
  social_media_link_3 = models.CharField(max_length=80, blank=True, null=True)

  is_active = models.BooleanField(default = True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)


  def save(self, *args, **kwargs):
    if self.user.role != "VENDOR":
      raise ValidationError("Only user with role 'VENDOR' can create a shop")
    
    super().save(*args, **kwargs)

  def __str__(self):
    return self.name