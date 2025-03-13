from django.db import models
from user.models import CustomUser

# Shop
class Shop(models.Model):
  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
  name = models.CharField(max_length=80)
  description = models.TextField()
  is_active = models.BooleanField(default = True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return self.name