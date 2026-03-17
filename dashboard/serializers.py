"""
Serializers for dashboard admin endpoints.
All serializers are read-only and used for data aggregation and reporting.
"""
from rest_framework import serializers
from users.models import User
from orders.models import Order, OrderItem
from products.models import ProductVariant
from drops.models import Drop


class DashboardStatsSerializer(serializers.Serializer):
    """
    Read-only serializer for dashboard statistics.
    Aggregates key metrics for the admin dashboard.
    """
    total_orders_today = serializers.IntegerField()
    total_orders_this_week = serializers.IntegerField()
    total_orders_this_month = serializers.IntegerField()
    revenue_today = serializers.IntegerField()  # Kobo
    revenue_today_naira = serializers.FloatField()
    revenue_this_week = serializers.IntegerField()  # Kobo
    revenue_this_week_naira = serializers.FloatField()
    revenue_this_month = serializers.IntegerField()  # Kobo
    revenue_this_month_naira = serializers.FloatField()
    total_customers = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    total_products = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()  # stock <= 5
    out_of_stock_count = serializers.IntegerField()  # stock = 0
    pending_orders = serializers.IntegerField()
    active_drops = serializers.IntegerField()


class RecentOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for recent orders list with customer and total info.
    """
    customer_email = serializers.CharField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    total_naira = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_number',
            'customer_email',
            'customer_name',
            'status',
            'payment_status',
            'total',
            'total_naira',
            'created_at'
        ]
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        """Return customer's full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_total_naira(self, obj):
        """Convert Kobo to Naira."""
        return obj.total / 100 if obj.total else 0


class LowStockSerializer(serializers.ModelSerializer):
    """
    Serializer for low stock product variants.
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_size = serializers.CharField(source='size', read_only=True)
    variant_colour = serializers.CharField(source='colour', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'product_name',
            'variant_size',
            'variant_colour',
            'sku',
            'stock_quantity'
        ]
        read_only_fields = fields


class TopProductSerializer(serializers.Serializer):
    """
    Read-only serializer for top-selling products.
    Aggregates sales data and revenue per product.
    """
    product_name = serializers.CharField()
    product_slug = serializers.CharField()
    total_units_sold = serializers.IntegerField()
    total_revenue = serializers.IntegerField()  # Kobo
    total_revenue_naira = serializers.FloatField()


class OrderStatusBreakdownSerializer(serializers.Serializer):
    """
    Read-only serializer for order status breakdown.
    Shows count and total value for each order status.
    """
    status = serializers.CharField()
    count = serializers.IntegerField()
    total_value = serializers.IntegerField()  # Kobo
    total_value_naira = serializers.FloatField()


class RevenueByDaySerializer(serializers.Serializer):
    """
    Read-only serializer for daily revenue data.
    Shows daily aggregates for the last 30 days.
    """
    date = serializers.DateField()
    order_count = serializers.IntegerField()
    revenue = serializers.IntegerField()  # Kobo
    revenue_naira = serializers.FloatField()


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for customer profiles with order and spending aggregates.
    """
    full_name = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    total_spent_naira = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone',
            'date_joined',
            'total_orders',
            'total_spent',
            'total_spent_naira'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        """Return customer's full name."""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_total_orders(self, obj):
        """Get total_orders from annotation or default to 0."""
        return getattr(obj, 'total_orders', 0) or 0
    
    def get_total_spent(self, obj):
        """Get total_spent from annotation or default to 0."""
        return getattr(obj, 'total_spent', 0) or 0
    
    def get_total_spent_naira(self, obj):
        """Convert Kobo to Naira."""
        total_spent = getattr(obj, 'total_spent', 0) or 0
        return total_spent / 100


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    """
    Full order detail serializer for admin view.
    Includes customer info and all order items.
    """
    customer_email = serializers.CharField(source='user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    total_naira = serializers.SerializerMethodField()
    subtotal_naira = serializers.SerializerMethodField()
    shipping_fee_naira = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_email',
            'customer_name',
            'status',
            'payment_status',
            'subtotal',
            'subtotal_naira',
            'shipping_fee',
            'shipping_fee_naira',
            'total',
            'total_naira',
            'items',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields
    
    def get_customer_name(self, obj):
        """Return customer's full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_total_naira(self, obj):
        return obj.total / 100 if obj.total else 0
    
    def get_subtotal_naira(self, obj):
        return obj.subtotal / 100 if obj.subtotal else 0
    
    def get_shipping_fee_naira(self, obj):
        return obj.shipping_fee / 100 if obj.shipping_fee else 0
    
    def get_items(self, obj):
        """Return serialized order items."""
        items = obj.items.all()
        return [
            {
                'id': item.id,
                'product_name': item.product_name,
                'variant_info': item.variant_info,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'unit_price_naira': item.unit_price / 100
            }
            for item in items
        ]
