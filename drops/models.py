from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from products.models import Product


class Drop(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='drops/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    launch_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-launch_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_live(self):
        now = timezone.now()
        if self.status != 'live':
            return False
        if self.end_date is not None:
            return self.launch_date <= now <= self.end_date
        return self.launch_date <= now

    @property
    def is_upcoming(self):
        now = timezone.now()
        return self.status == 'scheduled' and self.launch_date > now

    @property
    def countdown_seconds(self):
        if not self.is_upcoming:
            return 0
        delta = self.launch_date - timezone.now()
        return max(int(delta.total_seconds()), 0)

    @property
    def has_ended(self):
        now = timezone.now()
        if self.status == 'ended':
            return True
        return self.end_date is not None and self.end_date < now

    def activate(self):
        self.status = 'live'
        self.save()


class DropProduct(models.Model):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name='drop_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='drop_appearances')
    drop_price = models.PositiveIntegerField()
    quantity_limit = models.PositiveIntegerField(null=True, blank=True)
    units_sold = models.PositiveIntegerField(default=0)
    is_sold_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['drop', 'product']]

    def __str__(self):
        return f"{self.drop.name} — {self.product.name}"

    @property
    def drop_price_naira(self):
        return self.drop_price / 100

    @property
    def units_remaining(self):
        if self.quantity_limit is None:
            return None
        return max(self.quantity_limit - self.units_sold, 0)

    @property
    def discount_percentage(self):
        if self.product.price <= 0 or self.drop_price >= self.product.price:
            return 0
        return int(((self.product.price - self.drop_price) / self.product.price) * 100)
