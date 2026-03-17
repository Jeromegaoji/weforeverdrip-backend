import os
import django

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weforeverdrip_backend.settings')
    django.setup()

    from django.utils import timezone
    from datetime import timedelta
    from products.models import Product
    from drops.models import Drop, DropProduct

    now = timezone.now()
    drop1, created = Drop.objects.get_or_create(
        slug='ss25-launch-drop',
        defaults={
            'name': 'SS25 Launch Drop',
            'description': 'The first official WEFOREVERDRIP seasonal drop. Limited pieces. Real culture.',
            'status': 'live',
            'is_published': True,
            'launch_date': now - timedelta(days=7),
            'end_date': now + timedelta(days=7),
        },
    )
    print(f"Drop 1: {drop1.name} ({'created' if created else 'exists'})")
    drop1_updated = False
    if not created:
        drop1.name = 'SS25 Launch Drop'
        drop1.description = 'The first official WEFOREVERDRIP seasonal drop. Limited pieces. Real culture.'
        drop1.status = 'live'
        drop1.is_published = True
        drop1.launch_date = now - timedelta(days=7)
        drop1.end_date = now + timedelta(days=7)
        drop1.save()
        drop1_updated = True
    if drop1_updated:
        print('Updated Drop 1 fields')

    drop2, created = Drop.objects.get_or_create(
        slug='coal-city-pack',
        defaults={
            'name': 'Coal City Pack',
            'description': 'Enugu only energy. Limited to 100 units worldwide.',
            'status': 'scheduled',
            'is_published': True,
            'launch_date': now + timedelta(days=14),
            'end_date': now + timedelta(days=21),
        },
    )
    print(f"Drop 2: {drop2.name} ({'created' if created else 'exists'})")
    drop2_updated = False
    if not created:
        drop2.name = 'Coal City Pack'
        drop2.description = 'Enugu only energy. Limited to 100 units worldwide.'
        drop2.status = 'scheduled'
        drop2.is_published = True
        drop2.launch_date = now + timedelta(days=14)
        drop2.end_date = now + timedelta(days=21)
        drop2.save()
        drop2_updated = True
    if drop2_updated:
        print('Updated Drop 2 fields')

    drop_items = [
        (drop1, 'regular-white-tee', 1000000, 50),
        (drop1, 'navy-active-shorts', 1500000, 30),
        (drop2, 'wood-boxer-set', 800000, 100),
        (drop2, 'camo-bucket-hat', 600000, 100),
    ]

    for drop_obj, product_slug, drop_price, quantity_limit in drop_items:
        try:
            product = Product.objects.get(slug=product_slug)
        except Product.DoesNotExist:
            print(f"ERROR: Product not found: {product_slug}")
            continue

        dp, created = DropProduct.objects.get_or_create(
            drop=drop_obj,
            product=product,
            defaults={
                'drop_price': drop_price,
                'quantity_limit': quantity_limit,
            },
        )
        if created:
            print(f"Added {product.name} to {drop_obj.name} ({drop_price} Kobo, limit {quantity_limit})")
        else:
            dp.drop_price = drop_price
            dp.quantity_limit = quantity_limit
            dp.save()
            print(f"Updated {product.name} in {drop_obj.name} ({drop_price} Kobo, limit {quantity_limit})")

    print('Seed drops complete.')
