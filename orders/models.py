import uuid
from django.utils import timezone
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _

from products.models import Product
from user.models import User
from shop.models import Shop


class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order: {self.order.id})"
    
    def product_price(self):
        """Calculate the final price after discounts and vat"""
        final_price = self.product.base_price * (1 - self.product.discount_percents/100 + self.product.vat_percents/100) * self.quantity
        return final_price


class ShippingAddress(models.Model):
    order = models.OneToOneField('Order', related_name='shipping_address', on_delete=models.CASCADE)
    
    recipient_name = models.CharField(max_length=255)
    
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=50)
    state_province = models.CharField(max_length=50, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=50)
    
    def __str__(self):
        return f"Shipping Address for Order {self.order.id}"


class PaymentInfo(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', _('Stripe')),
        ('paypal', _('PayPal')),
        ('cash_on_delivery', _('Cash on Delivery')),
    ]
    
    order = models.OneToOneField('Order', related_name='payment', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.get_status_display()}"


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('cart', _('Cart')),
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('completed', _('Completed')),
        ('canceled', _('Canceled')),
        ('refunded', _('Refunded')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='cart')
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # additional cost per order
    sales_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Applied discounts
    coupon = models.ForeignKey('coupons.Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    campaigns = models.ManyToManyField('campaigns.Campaign', blank=True)

    # coupon_discount_percents = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # campaign_discount_percents = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    

    # Vendors tracking
    shops = models.ManyToManyField(Shop, related_name='orders', blank=True)
    
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        ordering = ['-created_at']
    
    def __str__(self):
        if self.order_number:
            return f"Order #{self.order_number}"
        return f"Cart {self.id}"
    
    def save(self, *args, **kwargs):
        # Generate order number on first save if it's not a cart
        if not self.order_number and self.status != 'cart':
            last_order = Order.objects.exclude(order_number=None).order_by('-created_at').first()
            if last_order and last_order.order_number:
                try:
                    number = int(last_order.order_number) + 1
                    self.order_number = f"{number:08d}"
                except (ValueError, TypeError):
                    self.order_number = f"{10001:08d}"
            else:
                self.order_number = f"{10001:08d}"
        
        # If status changes to completed, set completed timestamp
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate order totals based on items and applied discounts"""
        # Reset calculations
        self.subtotal = Decimal('0.00')
                
        # Calculate from order items
        for item in self.items.all():
            self.subtotal += item.base_price * item.quantity
            self.discount_amount += item.unit_discount * item.quantity
        
        # Apply order-level discounts from coupons and campaigns
        self.apply_coupon_discount()
        self.apply_campaign_discounts()
        
        # Calculate final total
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        
        # Make sure total is never negative
        if self.total_amount < 0:
            self.total_amount = Decimal('0.00')
            
        self.save()
        return self.total_amount
    
    def apply_coupon_discount(self):
        """Apply coupon discount to the order if valid"""
        if self.coupon and self.coupon.is_valid(self):
            discount = self.coupon.calculate_discount(self.subtotal)
            self.discount_amount += discount
            return discount
        return Decimal('0.00')
    
    def apply_campaign_discounts(self):
        """Apply campaign discounts to the order"""
        total_campaign_discount = Decimal('0.00')
        for campaign in self.campaigns.filter(is_active=True):
            discount = campaign.calculate_discount(self)
            self.discount_amount += discount
            total_campaign_discount += discount
        return total_campaign_discount
    
    def add_product(self, product, quantity=1):
        """Add a product to the order with the given quantity"""
        if self.status != 'cart':
            raise ValueError("Cannot add items to a non-cart order")
            
        # Get or create order item
        item, created = self.items.get_or_create(
            product=product,
            shop=product.shop,
            defaults={
                'base_price': product.price,
                'quantity': quantity,
                'final_price': product.price * quantity
            }
        )
        
        # Update quantity if item already exists
        if not created:
            item.quantity += quantity
            item.final_price = item.base_price * item.quantity
            item.save()
            
        # Update order shops
        self.shops.add(product.shop)
        
        # Recalculate order totals
        self.calculate_totals()
        return item
    
    def get_items_by_shop(self):
        """Group order items by shop"""
        items_by_shop = {}
        for item in self.items.all():
            if item.shop_id not in items_by_shop:
                items_by_shop[item.shop_id] = {
                    'shop': item.shop,
                    'items': [],
                    'subtotal': Decimal('0.00'),
                }
            items_by_shop[item.shop_id]['items'].append(item)
            items_by_shop[item.shop_id]['subtotal'] += item.final_price
        return items_by_shop
    
    def get_shop_totals(self):
        """Calculate totals for each shop in the order"""
        shop_totals = []
        items_by_shop = self.get_items_by_shop()
        
        for shop_id, data in items_by_shop.items():
            shop_totals.append({
                'shop': data['shop'],
                'items_count': len(data['items']),
                'subtotal': data['subtotal'],
                'commission': self.calculate_commission(data['shop'], data['subtotal']),
            })
        return shop_totals
    
    def calculate_commission(self, shop, amount):
        """Calculate platform commission for a shop's sales"""
        # This would integrate with your commission structure
        # For example, a flat 10% or variable based on shop type/tier
        return amount * Decimal('0.10')  # 10% commission
    
    def checkout(self):
        """Process cart checkout to pending order"""
        if self.status != 'cart':
            raise ValueError("Only carts can be checked out")
            
        if not self.items.exists():
            raise ValueError("Cannot checkout empty cart")
            
        # Update status
        self.status = 'pending'
        self.save()
        
        # This is where you would handle payment processing, inventory updates, etc.
        return True
