from django.db import models
from decimal import Decimal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from user.models import User


class CouponType(models.TextChoices):
    PERCENTAGE = 'percentage', _('Percentage Discount')
    FIXED_AMOUNT = 'fixed', _('Fixed Amount Discount')
    FREE_SHIPPING = 'shipping', _('Free Shipping')
    BUY_X_GET_Y = 'bxgy', _('Buy X Get Y Free')
    FIRST_ORDER = 'first_order', _('First Order Discount')


class CouponRestriction(models.Model):
    """Model for coupon usage restrictions"""
    coupon = models.OneToOneField('Coupon', related_name='restriction', on_delete=models.CASCADE)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(default=0, help_text=_("Max number of times this coupon can be used (0 = unlimited)"))
    usage_count = models.PositiveIntegerField(default=0, help_text=_("Number of times this coupon has been used"))
    
    # User limits
    per_user_limit = models.PositiveIntegerField(default=1, help_text=_("Max uses per user (0 = unlimited)"))
    
    # Order value limits
    minimum_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text=_("Minimum order subtotal required"))
    maximum_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text=_("Maximum order subtotal allowed (0 = no maximum)"))
    
    # Product/category restrictions
    products = models.ManyToManyField('products.Product', blank=True, help_text=_("Specific products this coupon applies to"))
    categories = models.ManyToManyField('products.Category', blank=True, help_text=_("Specific categories this coupon applies to"))
    shops = models.ManyToManyField('shop.Shop', blank=True, help_text=_("Specific shops this coupon applies to"))
    
    # User group restrictions
    user_groups = models.ManyToManyField('auth.Group', blank=True, help_text=_("User groups that can use this coupon"))
    
    # New customer only
    new_customers_only = models.BooleanField(default=False, help_text=_("Only for customers with no previous orders"))
    
    def __str__(self):
        return f"Restrictions for {self.coupon}"




class Coupon(models.Model):
    # Basic info
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    
    # Type and value
    type = models.CharField(max_length=20, choices=CouponType.choices, default=CouponType.PERCENTAGE)
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Max discount (for percentage discounts)
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text=_("Maximum discount amount for percentage discounts")
    )
    
    # Validity
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Ownership
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_coupons')
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE, null=True, blank=True, 
                            help_text=_("Shop that created this coupon (null for admin/platform coupons)"))
    
    # Created/updated timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
        ordering = ['-created_at']
    
    def __str__(self):
        if self.type == CouponType.PERCENTAGE:
            return f"{self.code} - {self.value}% off"
        elif self.type == CouponType.FIXED_AMOUNT:
            return f"{self.code} - ${self.value} off"
        elif self.type == CouponType.FREE_SHIPPING:
            return f"{self.code} - Free shipping"
        else:
            return f"{self.code} - {self.get_type_display()}"
    
    def is_valid(self, order=None):
        """Check if the coupon is valid for the given order"""
        now = timezone.now()
        
        # Check if coupon is active and within date range
        if not self.is_active:
            return False
            
        if now < self.start_date:
            return False
            
        if self.end_date and now > self.end_date:
            return False
        
        # If no order provided, just check basic validity
        if not order:
            return True
            
        # Check order-specific restrictions
        try:
            restriction = self.restriction
        except CouponRestriction.DoesNotExist:
            # No restrictions defined
            return True
            
        # Check usage limits
        if restriction.usage_limit > 0 and restriction.usage_count >= restriction.usage_limit:
            return False
            
        # Check per-user limits
        if restriction.per_user_limit > 0:
            user_usage = order.user.orders.filter(coupon=self).count()
            if user_usage >= restriction.per_user_limit:
                return False
        
        # Check minimum spend
        if restriction.minimum_spend > 0 and order.subtotal < restriction.minimum_spend:
            return False
            
        # Check maximum spend
        if restriction.maximum_spend > 0 and order.subtotal > restriction.maximum_spend:
            return False
            
        # Check new customer requirement
        if restriction.new_customers_only:
            previous_orders = order.user.orders.exclude(id=order.id).filter(status__in=['completed', 'delivered']).exists()
            if previous_orders:
                return False
        
        # Check product/category restrictions
        if restriction.products.exists() or restriction.categories.exists():
            valid_products = set(restriction.products.values_list('id', flat=True))
            valid_categories = set(restriction.categories.values_list('id', flat=True))
            
            # Get products and their categories in the order
            order_product_ids = set()
            order_category_ids = set()
            
            for item in order.items.all():
                order_product_ids.add(item.product.id)
                order_category_ids.add(item.product.category.id)
            
            # Check if any valid product/category is in the order
            if valid_products and not (valid_products & order_product_ids):
                return False
                
            if valid_categories and not (valid_categories & order_category_ids):
                return False
        
        # Check shop restrictions
        if restriction.shops.exists():
            valid_shops = set(restriction.shops.values_list('id', flat=True))
            order_shops = set(order.shops.values_list('id', flat=True))
            
            if not (valid_shops & order_shops):
                return False
        
        # Check user group restrictions
        if restriction.user_groups.exists():
            user_groups = set(order.user.groups.values_list('id', flat=True))
            valid_groups = set(restriction.user_groups.values_list('id', flat=True))
            
            if not (user_groups & valid_groups):
                return False
        
        return True
    
    def calculate_discount(self, subtotal):
        """Calculate the discount amount for a given subtotal"""
        if self.type == CouponType.PERCENTAGE:
            discount = subtotal * (self.value / 100)
            # Apply maximum discount if set
            if self.max_discount_amount and discount > self.max_discount_amount:
                discount = self.max_discount_amount
        elif self.type == CouponType.FIXED_AMOUNT:
            discount = min(self.value, subtotal)  # Don't exceed the subtotal
        elif self.type == CouponType.FREE_SHIPPING:
            # This would typically be handled separately in the order
            discount = Decimal('0.00')
        else:
            # Other coupon types would have custom logic
            discount = Decimal('0.00')
            
        return discount
    
    def increment_usage(self):
        """Increment the usage count of this coupon"""
        try:
            restriction = self.restriction
            restriction.usage_count += 1
            restriction.save()
        except CouponRestriction.DoesNotExist:
            pass

