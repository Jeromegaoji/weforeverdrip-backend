from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductVariant


class Command(BaseCommand):
    help = 'Seed the database with W∞D products'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding W∞D products...')

        # --- Categories ---
        tops, _ = Category.objects.get_or_create(
            slug='tops',
            defaults={'name': 'Tops', 'description': 'T-shirts and sweatshirts'}
        )
        bottoms, _ = Category.objects.get_or_create(
            slug='bottoms',
            defaults={'name': 'Bottoms', 'description': 'Shorts and trousers'}
        )
        accessories, _ = Category.objects.get_or_create(
            slug='accessories',
            defaults={'name': 'Accessories', 'description': 'Hats, beanies, socks and more'}
        )

        self.stdout.write('  ✓ Categories ready')

        # --- Products ---
        # price is stored in kobo (multiply naira by 100)
        products_data = [
            {
                'name': 'Regular White Tee',
                'slug': 'regular-white-tee',
                'description': 'A clean, heavyweight regular-fit tee in crisp white. The W∞D essential.',
                'category': tops,
                'price': 1500000,        # ₦15,000
                'compare_price': None,
                'is_featured': True,
                'variants': [
                    {'size': 'S',   'colour': 'White', 'sku': 'RWT-S',   'stock': 10},
                    {'size': 'M',   'colour': 'White', 'sku': 'RWT-M',   'stock': 15},
                    {'size': 'L',   'colour': 'White', 'sku': 'RWT-L',   'stock': 15},
                    {'size': 'XL',  'colour': 'White', 'sku': 'RWT-XL',  'stock': 10},
                    {'size': 'XXL', 'colour': 'White', 'sku': 'RWT-XXL', 'stock': 5},
                ],
            },
            {
                'name': 'Black Oversized Tee',
                'slug': 'black-oversized-tee',
                'description': 'Dropped shoulders, heavy cotton, deep black. Built for the streets.',
                'category': tops,
                'price': 1800000,        # ₦18,000
                'compare_price': None,
                'is_featured': True,
                'variants': [
                    {'size': 'S',   'colour': 'Black', 'sku': 'BOT-S',   'stock': 10},
                    {'size': 'M',   'colour': 'Black', 'sku': 'BOT-M',   'stock': 15},
                    {'size': 'L',   'colour': 'Black', 'sku': 'BOT-L',   'stock': 15},
                    {'size': 'XL',  'colour': 'Black', 'sku': 'BOT-XL',  'stock': 10},
                    {'size': 'XXL', 'colour': 'Black', 'sku': 'BOT-XXL', 'stock': 5},
                ],
            },
            {
                'name': 'Navy Active Shorts',
                'slug': 'navy-active-shorts',
                'description': 'Lightweight, breathable active shorts in navy. Move in them. Drip in them.',
                'category': bottoms,
                'price': 1600000,        # ₦16,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'S',   'colour': 'Navy', 'sku': 'NAS-S',   'stock': 8},
                    {'size': 'M',   'colour': 'Navy', 'sku': 'NAS-M',   'stock': 12},
                    {'size': 'L',   'colour': 'Navy', 'sku': 'NAS-L',   'stock': 12},
                    {'size': 'XL',  'colour': 'Navy', 'sku': 'NAS-XL',  'stock': 8},
                    {'size': 'XXL', 'colour': 'Navy', 'sku': 'NAS-XXL', 'stock': 4},
                ],
            },
            {
                'name': 'Camo Bucket Hat',
                'slug': 'camo-bucket-hats',
                'description': 'Classic camo bucket hat with the W∞D woven label. One size fits most.',
                'category': accessories,
                'price': 1000000,        # ₦10,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'ONE_SIZE', 'colour': 'Camo', 'sku': 'CBH-OS', 'stock': 20},
                ],
            },
            {
                'name': 'W∞D Black Beanie',
                'slug': 'wood-black-beanie',
                'description': 'Ribbed knit beanie in jet black. The W∞D logo hits different in winter.',
                'category': accessories,
                'price': 800000,         # ₦8,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'ONE_SIZE', 'colour': 'Black', 'sku': 'WBB-OS', 'stock': 20},
                ],
            },
            {
                'name': 'W∞D Boxer Set',
                'slug': 'wood-boxer-set',
                'description': 'Premium cotton boxer set. Two-pack. The drip starts from the inside.',
                'category': accessories,
                'price': 1200000,        # ₦12,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'S',   'colour': 'Mixed', 'sku': 'WBX-S',   'stock': 10},
                    {'size': 'M',   'colour': 'Mixed', 'sku': 'WBX-M',   'stock': 15},
                    {'size': 'L',   'colour': 'Mixed', 'sku': 'WBX-L',   'stock': 15},
                    {'size': 'XL',  'colour': 'Mixed', 'sku': 'WBX-XL',  'stock': 10},
                    {'size': 'XXL', 'colour': 'Mixed', 'sku': 'WBX-XXL', 'stock': 5},
                ],
            },
            {
                'name': 'W∞D Black Sweatshirt',
                'slug': 'wood-black-sweatshirt',
                'description': 'Heavyweight fleece sweatshirt in black. Oversized fit. W∞D chest embroidery.',
                'category': tops,
                'price': 2500000,        # ₦25,000
                'compare_price': None,
                'is_featured': True,
                'variants': [
                    {'size': 'S',   'colour': 'Black', 'sku': 'WBS-S',   'stock': 8},
                    {'size': 'M',   'colour': 'Black', 'sku': 'WBS-M',   'stock': 12},
                    {'size': 'L',   'colour': 'Black', 'sku': 'WBS-L',   'stock': 12},
                    {'size': 'XL',  'colour': 'Black', 'sku': 'WBS-XL',  'stock': 8},
                    {'size': 'XXL', 'colour': 'Black', 'sku': 'WBS-XXL', 'stock': 4},
                ],
            },
            {
                'name': 'W∞D White Sweatshirt',
                'slug': 'wood-white-sweatshirt',
                'description': 'Same heavyweight fleece silhouette in cream white. Clean and loud at once.',
                'category': tops,
                'price': 2500000,        # ₦25,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'S',   'colour': 'White', 'sku': 'WWS-S',   'stock': 8},
                    {'size': 'M',   'colour': 'White', 'sku': 'WWS-M',   'stock': 12},
                    {'size': 'L',   'colour': 'White', 'sku': 'WWS-L',   'stock': 12},
                    {'size': 'XL',  'colour': 'White', 'sku': 'WWS-XL',  'stock': 8},
                    {'size': 'XXL', 'colour': 'White', 'sku': 'WWS-XXL', 'stock': 4},
                ],
            },
            {
                'name': 'W∞D Socks',
                'slug': 'wood-socks',
                'description': 'Crew-length cotton socks with the W∞D logo woven into the ankle. Three-pack.',
                'category': accessories,
                'price': 500000,         # ₦5,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'ONE_SIZE', 'colour': 'Mixed', 'sku': 'WSK-OS', 'stock': 30},
                ],
            },
            {
                'name': 'W∞D Trucker Cap',
                'slug': 'wood-trucker-caps',
                'description': 'Mesh-back trucker cap with embroidered W∞D logo on the front panel.',
                'category': accessories,
                'price': 1200000,        # ₦12,000
                'compare_price': None,
                'is_featured': False,
                'variants': [
                    {'size': 'ONE_SIZE', 'colour': 'Black', 'sku': 'WTC-OS', 'stock': 20},
                ],
            },
        ]

        for data in products_data:
            variants_data = data.pop('variants')

            product, created = Product.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )

            if created:
                self.stdout.write(f'  ✓ Created: {product.name}')
            else:
                self.stdout.write(f'  – Already exists: {product.name}')

            for v in variants_data:
                ProductVariant.objects.get_or_create(
                    sku=v['sku'],
                    defaults={
                        'product': product,
                        'size': v['size'],
                        'colour': v['colour'],
                        'stock_quantity': v['stock'],
                    }
                )

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete!'))