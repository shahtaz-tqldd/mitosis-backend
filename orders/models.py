import uuid
from django.db import models
from products.models import Product
from user.models import User
from shop.models import Shop
from coupons.models import Coupon
from campaign.models import Campaign

class OrderItem(models.Model):
    order = models.ForeignKey('Orders', related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Order Item: {self.product.name} x {self.quantity}"

    def get_discounted_price(self):
        """Returns the price after discount."""
        return self.price * (1 - self.discount / 100)


class Orders(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('canceled', 'Canceled')
    ], default='pending')
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0) 
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.get_full_name()}"

    def calculate_total_price(self):
        """Calculates the total price of the order based on order items and potential discounts."""
        total = sum(item.quantity * item.get_discounted_price() for item in self.order_items.all())
        
        # Apply overall order discount (if any, from coupon or campaign)
        self.total_price = total * (1 - self.discount / 100)
        self.save()
        return self.total_price

    @property
    def order_items(self):
        """Retrieve the associated order items."""
        return OrderItem.objects.filter(order=self)

    def apply_coupon(self):
        """Apply coupon discount if available (can be extended for complex logic)."""
        if self.coupon:
            self.discount = self.coupon.discount_percentage
            self.save()

    def apply_campaign(self):
        """Apply campaign discount if available (can be extended for complex logic)."""
        if self.campaign:
            self.discount += self.campaign.discount_percentage  # Assuming campaign adds to the order discount
            self.save()
