from rest_framework import serializers
from django.utils import timezone

from products.serializers import ProductSerializer
from products.models import Product
from .models import Drop, DropProduct


class DropProductSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField(read_only=True)
    drop_price_naira = serializers.SerializerMethodField(read_only=True)
    units_remaining = serializers.SerializerMethodField(read_only=True)
    discount_percentage = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DropProduct
        fields = [
            'id',
            'product',
            'drop_price',
            'drop_price_naira',
            'quantity_limit',
            'units_sold',
            'units_remaining',
            'is_sold_out',
            'discount_percentage',
        ]

    def get_product(self, instance):
        return ProductSerializer(instance.product).data

    def get_drop_price_naira(self, instance):
        return instance.drop_price_naira

    def get_units_remaining(self, instance):
        return instance.units_remaining

    def get_discount_percentage(self, instance):
        return instance.discount_percentage


class DropSerializer(serializers.ModelSerializer):
    is_live = serializers.SerializerMethodField(read_only=True)
    is_upcoming = serializers.SerializerMethodField(read_only=True)
    countdown_seconds = serializers.SerializerMethodField(read_only=True)
    has_ended = serializers.SerializerMethodField(read_only=True)
    product_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Drop
        fields = [
            'id',
            'name',
            'slug',
            'cover_image',
            'status',
            'launch_date',
            'end_date',
            'is_live',
            'is_upcoming',
            'countdown_seconds',
            'has_ended',
            'product_count',
            'created_at',
        ]

    def get_is_live(self, instance):
        return instance.is_live

    def get_is_upcoming(self, instance):
        return instance.is_upcoming

    def get_countdown_seconds(self, instance):
        return instance.countdown_seconds

    def get_has_ended(self, instance):
        return instance.has_ended

    def get_product_count(self, instance):
        return instance.drop_products.count()


class DropDetailSerializer(DropSerializer):
    description = serializers.CharField(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    drop_products = serializers.SerializerMethodField(read_only=True)

    class Meta(DropSerializer.Meta):
        model = Drop
        fields = DropSerializer.Meta.fields + [
            'description',
            'is_published',
            'drop_products',
        ]

    def get_drop_products(self, instance):
        if instance.is_upcoming:
            return []
        return DropProductSerializer(instance.drop_products.all(), many=True).data


class DropWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drop
        fields = [
            'name',
            'description',
            'cover_image',
            'status',
            'launch_date',
            'end_date',
            'is_published',
        ]

    def validate(self, data):
        launch_date = data.get('launch_date', getattr(self.instance, 'launch_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))

        if launch_date and end_date and end_date <= launch_date:
            raise serializers.ValidationError({'end_date': 'end_date must be after launch_date.'})

        if self.instance is None and launch_date and launch_date < timezone.now():
            raise serializers.ValidationError({'launch_date': 'launch_date cannot be in the past.'})

        return data


class AddProductToDropSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')
    drop_price = serializers.IntegerField()
    quantity_limit = serializers.IntegerField(required=False, allow_null=True)

    def validate_drop_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('drop_price must be greater than 0.')
        return value

    def validate(self, data):
        drop = self.context.get('drop')
        product = data.get('product')
        if drop and product and DropProduct.objects.filter(drop=drop, product=product).exists():
            raise serializers.ValidationError('Product is already in this drop.')
        return data
