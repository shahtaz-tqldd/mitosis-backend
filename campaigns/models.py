from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from user.models import User


class CampaignType(models.TextChoices):
    SITE_WIDE = 'site_wide', _('Site-wide Sale')
    CATEGORY = 'category', _('Category Sale')
    SHOP = 'shop', _('Shop Sale')
    PRODUCT = 'product', _('Product Sale')
    FLASH_SALE = 'flash_sale', _('Flash Sale')
    SEASONAL = 'seasonal', _('Seasonal Promotion')
    BOGO = 'bogo', _('Buy One Get One')
    BUNDLE = 'bundle', _('Bundle Discount')


class Campaign(models.Model):
    # Basic info
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # Type and value
    campaign_type = models.CharField(max_length=20, choices=CampaignType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_percentage = models.BooleanField(default=True, help_text=_("Whether discount is a percentage or fixed amount"))
    
    # Validity
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Targeting
    categories = models.ManyToManyField('products.Category', blank=True, related_name='campaigns')
    products = models.ManyToManyField('products.Product', blank=True, related_name='campaigns')
    shops = models.ManyToManyField('shop.Shop', blank=True, related_name='campaigns')
    
    # Min purchase requirements
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_purchase_items = models.PositiveIntegerField(default=0)
    
    # Ownership and visibility
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField(default=True, help_text=_("Whether this campaign is visible to customers"))
    
    # Display
    banner_image = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    priority = models.PositiveIntegerField(default=0, help_text=_("Higher priority campaigns take precedence"))
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ['-priority', '-start_date']
    
    def __str__(self):
        return self.name
    
    def is_active_now(self):
        """Check if the campaign is currently active"""
        now = timezone.now()
        return (
            self.is_active and 
            self.start_date <= now and 
            self.end_date >= now
        )
    
    def calculate_discount(self, order):
        """Calculate discount amount for an order"""
        from decimal import Decimal
        
        if not self.is_active_now():
            return Decimal('0.00')
            
        # Check minimum purchase requirements
        if order.subtotal < self.min_purchase_amount:
            return Decimal('0.00')
            
        if self.min_purchase_items > 0 and order.items.count() < self.min_purchase_items:
            return Decimal('0.00')
        
        applicable_items = []
        
        # Filter items based on campaign type and targeting
        if self.campaign_type == CampaignType.SITE_WIDE:
            applicable_items = order.items.all()
            
        elif self.campaign_type == CampaignType.CATEGORY:
            category_ids = self.categories.values_list('id', flat=True)
            applicable_items = order.items.filter(product__category_id__in=category_ids)
            
        elif self.campaign_type == CampaignType.SHOP:
            shop_ids = self.shops.values_list('id', flat=True)
            applicable_items = order.items.filter(shop_id__in=shop_ids)
            
        elif self.campaign_type == CampaignType.PRODUCT:
            product_ids = self.products.values_list('id', flat=True)
            applicable_items = order.items.filter(product_id__in=product_ids)
            
        # Calculate applicable subtotal
        applicable_subtotal = sum(item.base_price * item.quantity for item in applicable_items)
        
        # Calculate discount
        if self.is_percentage:
            discount = applicable_subtotal * (self.discount_value / 100)
        else:
            discount = min(self.discount_value, applicable_subtotal)
            
        return discount
    
    def apply_to_product(self, product):
        """Calculate and return the discounted price for a product"""
        if not self.is_active_now():
            return product.price
            
        # Check if product is applicable for this campaign
        is_applicable = False
        
        if self.campaign_type == CampaignType.SITE_WIDE:
            is_applicable = True
            
        elif self.campaign_type == CampaignType.CATEGORY:
            is_applicable = self.categories.filter(id=product.category_id).exists()
            
        elif self.campaign_type == CampaignType.SHOP:
            is_applicable = self.shops.filter(id=product.shop_id).exists()
            
        elif self.campaign_type == CampaignType.PRODUCT:
            is_applicable = self.products.filter(id=product.id).exists()
            
        if not is_applicable:
            return product.price
            
        # Calculate discount
        if self.is_percentage:
            discount = product.price * (self.discount_value / 100)
        else:
            discount = min(self.discount_value, product.price)
            
        return product.price - discount


class CampaignPromoCode(models.Model):
    """Promo codes that can be used to access campaigns"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='promo_codes')
    code = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(default=0, help_text=_("Maximum number of uses (0 = unlimited)"))
    usage_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.code} - {self.campaign.name}"
    
    def increment_usage(self):
        """Increment the usage count of this promo code"""
        self.usage_count += 1
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            self.is_active = False
        self.save()


class CampaignTracking(models.Model):
    """Track campaign performance"""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='tracking')
    orders = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    views = models.PositiveIntegerField(default=0)
    conversions = models.PositiveIntegerField(default=0)
    date = models.DateField()
    
    class Meta:
        unique_together = ('campaign', 'date')
    
    def __str__(self):
        return f"{self.campaign.name} - {self.date}"
    
    @classmethod
    def record_order(cls, campaign, order):
        """Record an order for campaign tracking"""
        from django.utils import timezone
        today = timezone.now().date()
        
        tracking, created = cls.objects.get_or_create(
            campaign=campaign,
            date=today,
        )
        
        tracking.orders += 1
        tracking.revenue += order.total_amount
        tracking.discount_total += order.discount_amount
        tracking.conversions += 1
        tracking.save()