from rest_framework import serializers
from django.core.exceptions import ValidationError

from products.models import ProductVariant
from users.models import Address
from .models import Cart, CartItem, Order, OrderItem


class CartVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField(read_only=True)
    product_slug = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    price_naira = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'colour', 'sku', 'stock_quantity', 'in_stock', 'product_name', 'product_slug', 'price', 'price_naira']

    def get_product_name(self, instance):
        return instance.product.name

    def get_product_slug(self, instance):
        return instance.product.slug

    def get_price(self, instance):
        return instance.product.price

    def get_price_naira(self, instance):
        return instance.product.price_naira


class CartItemSerializer(serializers.ModelSerializer):
    variant = CartVariantSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)
    subtotal_naira = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'quantity', 'subtotal', 'subtotal_naira', 'added_at']

    def get_subtotal(self, instance):
        return instance.subtotal

    def get_subtotal_naira(self, instance):
        return instance.subtotal_naira


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField(read_only=True)
    total_naira = serializers.SerializerMethodField(read_only=True)
    item_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'total_naira', 'item_count', 'created_at']

    def get_total(self, instance):
        return instance.total

    def get_total_naira(self, instance):
        return instance.total_naira

    def get_item_count(self, instance):
        return instance.item_count


class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=10, default=1)

    def validate(self, data):
        variant = data['variant_id']
        quantity = data['quantity']
        if variant.stock_quantity < quantity:
            raise ValidationError('Not enough stock for selected variant.')
        return data


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField(read_only=True)
    subtotal_naira = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'variant_info', 'sku', 'quantity', 'unit_price', 'subtotal', 'subtotal_naira']
        read_only_fields = fields

    def get_subtotal(self, instance):
        return instance.subtotal

    def get_subtotal_naira(self, instance):
        return instance.subtotal_naira


class OrderSerializer(serializers.ModelSerializer):
    total_naira = serializers.SerializerMethodField(read_only=True)
    item_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'payment_status', 'total', 'total_naira', 'item_count', 'created_at']

    def get_total_naira(self, instance):
        return instance.total / 100

    def get_item_count(self, instance):
        return sum(item.quantity for item in instance.items.all())


class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    subtotal_naira = serializers.SerializerMethodField(read_only=True)
    shipping_fee_naira = serializers.SerializerMethodField(read_only=True)

    class Meta(OrderSerializer.Meta):
        model = Order
        fields = OrderSerializer.Meta.fields + [
            'items', 'shipping_address_snapshot', 'subtotal', 'subtotal_naira', 'shipping_fee', 'shipping_fee_naira', 'notes'
        ]

    def get_subtotal_naira(self, instance):
        return instance.subtotal / 100

    def get_shipping_fee_naira(self, instance):
        return instance.shipping_fee / 100


class PlaceOrderSerializer(serializers.Serializer):
    shipping_address_id = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        address = data.get('shipping_address_id')
        if address.user != user:
            raise ValidationError('Shipping address must belong to the logged-in user.')
        return data
