import uuid
from django.db import models
from django.utils.text import slugify
from app.utils import constants
from shop.models import Shop
from user.models import CustomUser
from django.contrib.postgres.fields import ArrayField 
from django.core.exceptions import ValidationError

# Category Model
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subcategories')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# Product Model
class Product(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=1200)
    body_html = models.TextField(blank=True, null=True)

    tags = ArrayField(models.CharField(max_length=50), blank=True, default=list)

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percents = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")

    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=50, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    updated_at = models.DateTimeField(auto_now=True)

    is_restricted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        """Generate a unique slug if not provided"""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def get_discounted_price(self):
        """Returns the price after discount"""
        return self.base_price - (self.base_price * (self.discount_percents / 100))

    def is_in_stock(self):
        """Check if the product is in stock"""
        return self.stock > 0

    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name
    
    
class AttributeValue(models.Model):
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=80)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default = uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=200)
    attributes = models.ManyToManyField(AttributeValue, related_name='variants')
    sku = models.CharField(max_length=80, unique=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percents = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    is_active = models.BooleanField(default=True)
    stock  = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'sku')
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]

    def get_discounted_price(self):
        return self.base_price - (self.base_price * (self.discount_percents/100))
    
    def is_in_stock(self):
        return self.stock > 0

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', null=True, blank=True)

    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(product__isnull=False) | models.Q(variant__isnull=False),
                name='products_or_variant_required'
            )
        ]

    def clean(self):
        """Customize function to store a limited number of image for each product or variants"""
        if self.product:
            image_count = ProductImage.objects.filter(product=self.product).count()
        
        elif self.variant:
            image_count = ProductImage.objects.filter(variant=self.variant).count()
        
        else:
            image_count = 0

        if image_count >= constants.MAX_IMAGE_COUNT:
            raise ValidationError(f"More than {constants.MAX_IMAGE_COUNT} images cannot be added!")


    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.product.name or self.variant.name}"