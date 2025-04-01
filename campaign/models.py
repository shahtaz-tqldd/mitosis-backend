from django.db import models
from django.utils.timezone import now

# Create your models here.
class Campaign(models.Model):
    name = models.CharField(max_length=255)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"Campaign {self.name} - {self.discount_percentage}%"

    def is_active(self):
        """Check if the campaign is currently active."""
        return self.start_date <= now() <= self.end_date
