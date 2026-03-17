import os
import django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weforeverdrip_backend.settings')
    django.setup()

    from products.models import Category, Product, ProductVariant

    categories_data = [
        {'name': 'Tees', 'slug': 'tees'},
        {'name': 'Shorts', 'slug': 'shorts'},
        {'name': 'Headwear', 'slug': 'headwear'},
        {'name': 'Intimates', 'slug': 'intimates'},
    ]

    created_categories = []
    for data in categories_data:
        category, created = Category.objects.get_or_create(slug=data['slug'], defaults={'name': data['name']})
        print(f"Category: {category.name} ({'created' if created else 'exists'})")
        created_categories.append(category)

    def get_category(slug):
        return Category.objects.get(slug=slug)

    products_data = [
        {
            'name': 'Regular White Tee',
            'slug': 'regular-white-tee',
            'category': get_category('tees'),
            'price': 1200000,
            'is_featured': True,
            'variants': [
                ('S', 'White', 10),
                ('M', 'White', 15),
                ('L', 'White', 8),
                ('XL', 'White', 5),
            ],
        },
        {
            'name': 'Black Oversized Tee',
            'slug': 'black-oversized-tee',
            'category': get_category('tees'),
            'price': 1500000,
            'is_featured': True,
            'variants': [
                ('S', 'Black', 8),
                ('M', 'Black', 12),
                ('L', 'Black', 10),
                ('XL', 'Black', 6),
            ],
        },
        {
            'name': 'Navy Active Shorts',
            'slug': 'navy-active-shorts',
            'category': get_category('shorts'),
            'price': 1850000,
            'is_featured': True,
            'variants': [
                ('S', 'Navy', 10),
                ('M', 'Navy', 8),
                ('L', 'Navy', 6),
                ('XL', 'Navy', 4),
            ],
        },
        {
            'name': 'Camo Bucket Hat',
            'slug': 'camo-bucket-hat',
            'category': get_category('headwear'),
            'price': 800000,
            'is_featured': False,
            'variants': [
                ('ONE_SIZE', 'Camo', 20),
            ],
        },
        {
            'name': 'WOOD Black Beanie',
            'slug': 'wood-black-beanie',
            'category': get_category('headwear'),
            'price': 650000,
            'is_featured': False,
            'variants': [
                ('ONE_SIZE', 'Black', 15),
            ],
        },
        {
            'name': 'WOOD Boxer Set',
            'slug': 'wood-boxer-set',
            'category': get_category('intimates'),
            'price': 950000,
            'is_featured': True,
            'variants': [
                ('S', 'Grey', 20),
                ('M', 'Grey', 20),
                ('L', 'Grey', 15),
                ('XL', 'Grey', 10),
            ],
        },
    ]

    created_products = 0
    created_variants = 0

    for pdata in products_data:
        product, created = Product.objects.get_or_create(
            slug=pdata['slug'],
            defaults={
                'name': pdata['name'],
                'description': pdata['name'],
                'category': pdata['category'],
                'price': pdata['price'],
                'compare_price': None,
                'is_active': True,
                'is_featured': pdata['is_featured'],
            },
        )
        if created:
            created_products += 1
            print(f"Created product: {product.name}")
        else:
            updated = False
            if product.name != pdata['name']:
                product.name = pdata['name']; updated = True
            if product.price != pdata['price']:
                product.price = pdata['price']; updated = True
            if product.is_featured != pdata['is_featured']:
                product.is_featured = pdata['is_featured']; updated = True
            if product.category != pdata['category']:
                product.category = pdata['category']; updated = True
            if updated:
                product.save()
                print(f"Updated product: {product.name}")

        for size, colour, stock in pdata['variants']:
            sku = f"{product.slug}-{size}-{colour}".lower().replace(' ', '-')
            variant, v_created = ProductVariant.objects.get_or_create(
                sku=sku,
                defaults={
                    'product': product,
                    'size': size,
                    'colour': colour,
                    'stock_quantity': stock,
                },
            )
            if v_created:
                created_variants += 1
                print(f"Created variant: {variant.sku} ({stock})")
            else:
                if variant.stock_quantity != stock:
                    variant.stock_quantity = stock
                    variant.save()
                print(f"Variant exists: {variant.sku} (stock={variant.stock_quantity})")

    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    print(f"Seed complete: {total_categories} categories, {total_products} products, {created_variants} variant creations.")
