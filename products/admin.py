from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductVariant,
    AttributeValue,
    ProductAttribute,
    ProductImage,
)


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "parent", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    ordering = ("created_at",)


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "shop",
        "base_price",
        "stock",
        "status",
        "created_at",
    )
    search_fields = ("name", "sku")
    list_filter = ("status", "category", "shop")
    ordering = ("created_at",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

    get_discounted_price.short_description = "Discounted Price"


# Product Variant Admin
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "base_price", "stock", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active", "product")
    ordering = ("created_at",)


# Product Attribute Admin
@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# Attribute Value Admin
@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ("id", "attribute", "value")
    search_fields = ("value",)


# Product Image Admin
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "variant")
    search_fields = ("alt_text",)
