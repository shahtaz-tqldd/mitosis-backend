from django.contrib import admin
from .models import Shop
# Register your models here.

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
  list_display = ("name", "user_name", "is_active")
  search_fields = ("name",)
  list_filter= ("is_active",)

  ordering = ("created_at",)

  def user_name(self, obj):
    return obj.user.get_full_name()
  
  user_name.short_description = "Vendor Name"