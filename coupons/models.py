from django.db import models
from django.utils.timezone import now

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 10.0 for 10% off
    expiry_date = models.DateTimeField()

    def __str__(self):
        return f"Coupon {self.code} - {self.discount_percentage}%"

    def is_valid(self):
        """Check if the coupon is still valid."""
        return self.expiry_date > now()
