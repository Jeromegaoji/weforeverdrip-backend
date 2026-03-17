from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'total_naira', 'created_at']
    search_fields = ['user__email']

    def total_naira(self, obj):
        return obj.total_naira

    def item_count(self, obj):
        return obj.item_count


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'variant', 'quantity', 'subtotal_naira']

    def subtotal_naira(self, obj):
        return obj.subtotal_naira


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total_naira', 'created_at']
    list_filter = ['status', 'payment_status']
    search_fields = ['order_number', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at']

    def total_naira(self, obj):
        return obj.total / 100


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'variant_info', 'quantity', 'unit_price', 'subtotal_naira']

    def subtotal_naira(self, obj):
        return obj.subtotal_naira
