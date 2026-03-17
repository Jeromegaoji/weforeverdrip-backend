"""
Tests for Drops API endpoints.
Tests drops listing, filtering, and admin operations.
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status

from drops.models import Drop, DropProduct
from products.models import Product


@pytest.mark.django_db
class TestDropEndpoints:
    """Test drop list and detail endpoints."""

    def create_drop(self, name, slug, status='live', is_published=True, start_date=None):
        """Helper to create a drop."""
        if start_date is None:
            start_date = timezone.now() if status == 'live' else timezone.now() + timedelta(days=7)

        return Drop.objects.create(
            name=name,
            slug=slug,
            description='Test drop',
            status=status,
            is_published=is_published,
            launch_date=start_date
        )

    def test_list_published_drops(self, api_client):
        """GET /api/v1/drops/ should only show published drops."""
        # Create published drop
        self.create_drop('Published Drop', 'published-drop', is_published=True)
        # Create unpublished drop
        self.create_drop('Unpublished Drop', 'unpublished-drop', is_published=False)

        response = api_client.get('/api/v1/drops/')

        assert response.status_code == status.HTTP_200_OK
        drops = response.data if isinstance(response.data, list) else response.data.get('results', [])
        drop_slugs = [d['slug'] for d in drops]
        assert 'published-drop' in drop_slugs
        assert 'unpublished-drop' not in drop_slugs

    def test_unpublished_drop_hidden(self, api_client):
        """Unpublished drops should not appear in list."""
        self.create_drop('Unpublished Drop', 'unpublished-drop', is_published=False)

        response = api_client.get('/api/v1/drops/')

        drops = response.data if isinstance(response.data, list) else response.data.get('results', [])
        drop_slugs = [d['slug'] for d in drops]
        assert 'unpublished-drop' not in drop_slugs

    def test_live_drops(self, api_client):
        """GET /api/v1/drops/live/ should only return status='live' drops."""
        self.create_drop('Live Drop', 'live-drop', status='live', is_published=True)
        self.create_drop('Scheduled Drop', 'scheduled-drop', status='scheduled', is_published=True)

        response = api_client.get('/api/v1/drops/live/')

        assert response.status_code == status.HTTP_200_OK
        drops = response.data if isinstance(response.data, list) else response.data.get('results', [])
        drop_slugs = [d['slug'] for d in drops]
        assert 'live-drop' in drop_slugs
        assert 'scheduled-drop' not in drop_slugs

    def test_upcoming_drops(self, api_client):
        """GET /api/v1/drops/upcoming/ should return scheduled future drops."""
        future_date = timezone.now() + timedelta(days=7)
        self.create_drop(
            'Upcoming Drop',
            'upcoming-drop',
            status='scheduled',
            is_published=True,
            start_date=future_date
        )

        response = api_client.get('/api/v1/drops/upcoming/')

        assert response.status_code == status.HTTP_200_OK
        drops = response.data if isinstance(response.data, list) else response.data.get('results', [])
        drop_slugs = [d['slug'] for d in drops]
        assert 'upcoming-drop' in drop_slugs

    def test_upcoming_drop_hides_products(self, api_client, sample_product):
        """Scheduled drops should not show products in response."""
        future_date = timezone.now() + timedelta(days=7)
        drop = self.create_drop(
            'Scheduled Drop',
            'scheduled-drop',
            status='scheduled',
            is_published=True,
            start_date=future_date
        )
        # Add product to drop
        DropProduct.objects.create(drop=drop, product=sample_product, drop_price=1000000)

        response = api_client.get(f'/api/v1/drops/{drop.slug}/')

        assert response.status_code == status.HTTP_200_OK
        # Products should be empty or hidden for scheduled drops
        assert response.data.get('drop_products', []) == []

    def test_live_drop_shows_products(self, api_client, sample_product):
        """Live drops should show products."""
        drop = self.create_drop('Live Drop', 'live-drop', status='live', is_published=True)
        DropProduct.objects.create(drop=drop, product=sample_product, drop_price=1000000)

        response = api_client.get(f'/api/v1/drops/{drop.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get('drop_products', [])) > 0

    def test_countdown_seconds_positive(self, api_client):
        """Upcoming drop should have positive countdown_seconds."""
        future_date = timezone.now() + timedelta(days=7)
        drop = self.create_drop(
            'Countdown Drop',
            'countdown-drop',
            status='scheduled',
            start_date=future_date
        )

        response = api_client.get(f'/api/v1/drops/{drop.slug}/')

        assert response.status_code == status.HTTP_200_OK
        countdown = response.data.get('countdown_seconds', 0)
        assert countdown > 0

    def test_discount_percentage(self, api_client, sample_product):
        """Drop with lower price should show discount percentage."""
        drop = self.create_drop('Discount Drop', 'discount-drop', status='live')
        original_price = sample_product.price  # 1,200,000
        drop_price = 1000000  # Lower price

        DropProduct.objects.create(drop=drop, product=sample_product, drop_price=drop_price)

        response = api_client.get(f'/api/v1/drops/{drop.slug}/')

        assert response.status_code == status.HTTP_200_OK
        drop_products = response.data.get('drop_products', [])
        if drop_products:
            discount = drop_products[0].get('discount_percentage', 0)
            assert discount > 0


@pytest.mark.django_db
class TestAdminDropEndpoints:
    """Test admin-only drop operations."""

    def test_create_drop_as_admin(self, admin_client):
        """Admin should be able to create drops."""
        data = {
            'name': 'New Drop',
            'slug': 'new-drop',
            'description': 'Test drop',
            'status': 'scheduled',
            'is_published': False,
            'launch_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = admin_client.post('/api/v1/drops/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Drop.objects.filter(slug='new-drop').exists()

    def test_create_drop_as_regular_user(self, auth_client):
        """Regular user should not create drops (403)."""
        data = {
            'name': 'Unauthorized Drop',
            'slug': 'unauthorized-drop',
            'status': 'scheduled'
        }
        response = auth_client.post('/api/v1/drops/', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_activate_drop(self, admin_client):
        """Admin should activate drop (change status to 'live')."""
        drop = Drop.objects.create(
            name='To Activate',
            slug='to-activate',
            status='scheduled',
            launch_date=timezone.now()
        )

        response = admin_client.post(f'/api/v1/drops/{drop.slug}/activate/')

        assert response.status_code == status.HTTP_200_OK
        drop.refresh_from_db()
        assert drop.status == 'live'

    def test_add_product_to_drop(self, admin_client, sample_product):
        """Admin should add product to drop."""
        drop = Drop.objects.create(
            name='Drop For Products',
            slug='drop-for-products',
            launch_date=timezone.now()
        )

        data = {
            'product_id': sample_product.id,
            'drop_price': 1000000
        }
        response = admin_client.post(f'/api/v1/drops/{drop.slug}/products/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert DropProduct.objects.filter(drop=drop, product=sample_product).exists()

    def test_remove_product_from_drop(self, admin_client, sample_product):
        """Admin should remove product from drop."""
        drop = Drop.objects.create(
            name='Drop For Removal',
            slug='drop-for-removal',
            launch_date=timezone.now()
        )
        drop_product = DropProduct.objects.create(
            drop=drop,
            product=sample_product,
            drop_price=1000000
        )

        response = admin_client.delete(f'/api/v1/drops/{drop.slug}/products/{drop_product.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DropProduct.objects.filter(id=drop_product.id).exists()
