from rest_framework import serializers

from .models import Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'created_at']
        read_only_fields = ['slug', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary']


class ProductVariantSerializer(serializers.ModelSerializer):
    in_stock = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'size', 'colour', 'sku', 'stock_quantity', 'in_stock']

    def get_in_stock(self, instance):
        return instance.in_stock


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    price_naira = serializers.SerializerMethodField(read_only=True)
    compare_price_naira = serializers.SerializerMethodField(read_only=True)
    is_on_sale = serializers.SerializerMethodField(read_only=True)
    primary_image = serializers.SerializerMethodField(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'category',
            'price',
            'price_naira',
            'compare_price',
            'compare_price_naira',
            'is_on_sale',
            'is_active',
            'is_featured',
            'created_at',
            'primary_image',
            'variants'
        ]

    def get_price_naira(self, instance):
        return instance.price_naira

    def get_compare_price_naira(self, instance):
        return instance.compare_price_naira

    def get_is_on_sale(self, instance):
        return instance.is_on_sale

    def get_primary_image(self, instance):
        primary = instance.images.filter(is_primary=True).first()
        if not primary:
            primary = instance.images.first()
        if primary:
            return ProductImageSerializer(primary).data
        return None


class ProductDetailSerializer(ProductSerializer):
    description = serializers.CharField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        model = Product
        fields = ProductSerializer.Meta.fields + ['description', 'images', 'variants']


class CategoryDetailSerializer(CategorySerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['products']


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'category',
            'price',
            'compare_price',
            'is_active',
            'is_featured',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than 0 Kobo.')
        return value

    def validate(self, data):
        compare_price = data.get('compare_price')
        price = data.get('price')
        if compare_price is not None and price is not None and compare_price <= price:
            raise serializers.ValidationError({'compare_price': 'compare_price must be greater than price.'})
        return data
