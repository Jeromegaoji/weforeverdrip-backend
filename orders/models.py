import datetime
import random

from django.conf import settings
from django.db import models


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

    @property
    def total(self):
        total = 0
        for item in self.items.all():
            total += item.subtotal
        return total

    @property
    def total_naira(self):
        return self.total / 100

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['cart', 'variant']]

    def __str__(self):
        return f"{self.quantity}x {self.variant}"

    @property
    def subtotal(self):
        return self.quantity * self.variant.product.price

    @property
    def subtotal_naira(self):
        return self.subtotal / 100


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    payment_reference = models.CharField(max_length=255, blank=True)
    shipping_address = models.ForeignKey('users.Address', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address_snapshot = models.JSONField(default=dict)
    subtotal = models.PositiveIntegerField(default=0)
    shipping_fee = models.PositiveIntegerField(default=150000)
    total = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_str = datetime.date.today().strftime('%Y%m%d')
            self.order_number = f"WFD-{date_str}-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=255)
    variant_info = models.CharField(max_length=100)
    sku = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def subtotal_naira(self):
        return self.subtotal / 100
