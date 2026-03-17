"""
Tests for Products API endpoints.
Tests categories, products, filtering, and admin operations.
"""
import pytest
from rest_framework import status

from products.models import Product, Category


@pytest.mark.django_db
class TestCategoryEndpoints:
    """Test category list and detail endpoints."""

    def test_list_categories(self, api_client, sample_category):
        """GET /api/v1/products/categories/ should return 200."""
        response = api_client.get('/api/v1/products/categories/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_category_detail(self, api_client, sample_category):
        """GET /api/v1/products/categories/<slug>/ should return 200."""
        response = api_client.get(f'/api/v1/products/categories/{sample_category.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Tees'


@pytest.mark.django_db
class TestProductEndpoints:
    """Test product list and detail endpoints."""

    def test_list_products(self, api_client, sample_product):
        """GET /api/v1/products/ should return paginated list."""
        response = api_client.get('/api/v1/products/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)

    def test_product_detail(self, api_client, sample_product):
        """GET /api/v1/products/<slug>/ should return 200."""
        response = api_client.get(f'/api/v1/products/{sample_product.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Tee'
        assert response.data['price'] == 1200000

    def test_inactive_product_hidden(self, api_client, sample_product):
        """Inactive products should return 404."""
        sample_product.is_active = False
        sample_product.save()

        response = api_client.get(f'/api/v1/products/{sample_product.slug}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_by_category(self, api_client, sample_product, sample_category):
        """Filter by category should return only products in that category."""
        response = api_client.get(f'/api/v1/products/?category={sample_category.slug}')

        assert response.status_code == status.HTTP_200_OK
        # Should contain at least the sample product
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        product_slugs = [p['slug'] for p in data]
        assert 'test-tee' in product_slugs

    def test_search_products(self, api_client, sample_product):
        """Search should find products by name."""
        response = api_client.get('/api/v1/products/?search=tee')

        assert response.status_code == status.HTTP_200_OK
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        assert len(data) >= 1

    def test_featured_products(self, api_client, sample_product, sample_category):
        """GET /api/v1/products/featured/ should return only featured products."""
        # Mark product as featured
        sample_product.is_featured = True
        sample_product.save()

        response = api_client.get('/api/v1/products/featured/')

        assert response.status_code == status.HTTP_200_OK
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # At least the sample product should be there
        assert len(data) >= 1


@pytest.mark.django_db
class TestAdminProductEndpoints:
    """Test admin-only product operations."""

    def test_create_product_as_admin(self, admin_client, sample_category):
        """Admin should be able to create products."""
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'description': 'A new product',
            'price': 500000,
            'category': sample_category.id,
            'is_active': True
        }
        response = admin_client.post('/api/v1/products/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(slug='new-product').exists()

    def test_create_product_as_regular_user(self, auth_client):
        """Regular user should not be able to create products (403)."""
        data = {
            'name': 'Unauthorized Product',
            'slug': 'unauthorized-product',
            'price': 500000
        }
        response = auth_client.post('/api/v1/products/', data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_unauthenticated(self, api_client):
        """Unauthenticated user should get 401."""
        data = {
            'name': 'No Auth Product',
            'slug': 'no-auth-product',
            'price': 500000
        }
        response = api_client.post('/api/v1/products/', data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_soft_delete_product(self, admin_client, sample_product):
        """DELETE should soft delete (set is_active=False)."""
        product_id = sample_product.id
        response = admin_client.delete(f'/api/v1/products/{sample_product.slug}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Product should still exist in DB but be inactive
        product = Product.objects.get(id=product_id)
        assert product.is_active is False

    def test_update_stock(self, admin_client, sample_variant):
        """PATCH variant should update stock_quantity."""
        data = {'stock_quantity': 25}
        response = admin_client.patch(
            f'/api/v1/products/variants/{sample_variant.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        sample_variant.refresh_from_db()
        assert sample_variant.stock_quantity == 25
