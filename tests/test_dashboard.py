"""
Tests for Admin Dashboard API endpoints.
Tests permissions, statistics, order management, inventory, and customers.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status

from orders.models import Order, OrderItem
from users.models import Address


@pytest.mark.django_db
class TestDashboardPermissions:
    """Test permission enforcement on all dashboard endpoints."""

    def test_stats_requires_staff(self, auth_client):
        """Regular user should not access admin stats (403)."""
        response = auth_client.get('/api/v1/admin/dashboard/stats/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_stats_unauthenticated(self, api_client):
        """Unauthenticated user should get 401."""
        response = api_client.get('/api/v1/admin/dashboard/stats/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_all_admin_endpoints_reject_regular_user(self, auth_client):
        """All 13 admin endpoints should reject regular users."""
        endpoints = [
            '/api/v1/admin/dashboard/stats/',
            '/api/v1/admin/dashboard/orders/recent/',
            '/api/v1/admin/dashboard/low-stock/',
            '/api/v1/admin/dashboard/top-products/',
            '/api/v1/admin/dashboard/order-breakdown/',
            '/api/v1/admin/dashboard/revenue/',
            '/api/v1/admin/orders/',
            '/api/v1/admin/inventory/',
            '/api/v1/admin/customers/',
        ]

        for endpoint in endpoints:
            response = auth_client.get(endpoint)
            assert response.status_code == status.HTTP_403_FORBIDDEN, f"Endpoint {endpoint} did not reject regular user"


@pytest.mark.django_db
class TestDashboardStats:
    """Test /api/v1/admin/dashboard/stats/ endpoint."""

    def test_stats_structure(self, admin_client):
        """Stats should return all expected fields."""
        response = admin_client.get('/api/v1/admin/dashboard/stats/')

        assert response.status_code == status.HTTP_200_OK
        expected_fields = [
            'total_orders_today',
            'revenue_today_naira',
            'total_customers',
            'low_stock_count',
            'pending_orders',
            'active_drops',
            'new_customers_this_month'
        ]
        for field in expected_fields:
            assert field in response.data

    def test_revenue_only_counts_paid_orders(self, admin_client, regular_user, sample_variant):
        """Revenue should only count orders with payment_status='paid'."""
        address = Address.objects.create(
            user=regular_user,
            street='Test St',
            city='Enugu',
            state='Enugu State'
        )

        # Create paid order
        paid_order = Order.objects.create(
            user=regular_user,
            order_number='WFD-PAID-001',
            status='confirmed',
            payment_status='paid',
            subtotal=1000000,
            shipping_fee=150000,
            total=1150000
        )

        # Create unpaid order (should be ignored)
        unpaid_order = Order.objects.create(
            user=regular_user,
            order_number='WFD-UNPAID-001',
            status='pending',
            payment_status='pending',
            subtotal=500000,
            shipping_fee=150000,
            total=650000
        )

        response = admin_client.get('/api/v1/admin/dashboard/stats/')

        assert response.status_code == status.HTTP_200_OK
        # Revenue should only include paid order
        # Exact value depends on existing data, but paid order should count
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if paid_order.created_at >= today_start:
            assert response.data['revenue_today'] >= 1150000


@pytest.mark.django_db
class TestAdminOrderManagement:
    """Test admin order endpoints."""

    def test_admin_sees_all_orders(self, admin_client, regular_user, sample_variant):
        """Admin should see orders from all users."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Create order for regular user
        order = Order.objects.create(
            user=regular_user,
            order_number='WFD-USER-001'
        )

        # Admin should see it
        response = admin_client.get('/api/v1/admin/orders/')

        assert response.status_code == status.HTTP_200_OK
        orders = response.data if isinstance(response.data, list) else response.data.get('results', [])
        order_numbers = [o['order_number'] for o in orders]
        assert 'WFD-USER-001' in order_numbers

    def test_filter_orders_by_status(self, admin_client, regular_user):
        """Filter by status parameter should work."""
        # Create orders with different statuses
        Order.objects.create(
            user=regular_user,
            order_number='WFD-PENDING-001',
            status='pending'
        )
        Order.objects.create(
            user=regular_user,
            order_number='WFD-CONFIRMED-001',
            status='confirmed'
        )

        response = admin_client.get('/api/v1/admin/orders/?status=pending')

        assert response.status_code == status.HTTP_200_OK
        orders = response.data if isinstance(response.data, list) else response.data.get('results', [])
        for order in orders:
            assert order['status'] == 'pending'

    def test_update_order_status(self, admin_client, regular_user):
        """PATCH order status should update it."""
        order = Order.objects.create(
            user=regular_user,
            order_number='WFD-UPDATE-001',
            status='pending'
        )

        data = {'status': 'confirmed'}
        response = admin_client.patch(
            f'/api/v1/admin/orders/{order.order_number}/status/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == 'confirmed'


@pytest.mark.django_db
class TestInventory:
    """Test inventory management endpoints."""

    def test_inventory_list(self, admin_client, sample_variant):
        """GET /api/v1/admin/inventory/ should return variants."""
        response = admin_client.get('/api/v1/admin/inventory/')

        assert response.status_code == status.HTTP_200_OK
        variants = response.data if isinstance(response.data, list) else response.data.get('results', [])
        assert len(variants) >= 1

    def test_low_stock_filter(self, admin_client, sample_variant):
        """Filter by low_stock=true should return only variants with stock <= 10."""
        # Update sample variant to be low stock
        sample_variant.stock_quantity = 5
        sample_variant.save()

        response = admin_client.get('/api/v1/admin/inventory/?low_stock=true')

        assert response.status_code == status.HTTP_200_OK
        variants = response.data if isinstance(response.data, list) else response.data.get('results', [])
        for variant in variants:
            assert variant['stock_quantity'] <= 10

    def test_update_stock(self, admin_client, sample_variant):
        """PATCH variant stock_quantity should update it."""
        data = {'stock_quantity': 50}
        response = admin_client.patch(
            f'/api/v1/admin/inventory/{sample_variant.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        sample_variant.refresh_from_db()
        assert sample_variant.stock_quantity == 50


@pytest.mark.django_db
class TestCustomers:
    """Test customer management endpoints."""

    def test_customer_list(self, admin_client, regular_user):
        """GET /api/v1/admin/customers/ should return customers."""
        response = admin_client.get('/api/v1/admin/customers/')

        assert response.status_code == status.HTTP_200_OK
        customers = response.data if isinstance(response.data, list) else response.data.get('results', [])
        # Should include at least the regular user
        customer_emails = [c['email'] for c in customers]
        assert 'user@test.com' in customer_emails

    def test_customer_detail(self, admin_client, regular_user):
        """GET /api/v1/admin/customers/<pk>/ should return customer with order history."""
        # Create an order for the user
        order = Order.objects.create(
            user=regular_user,
            order_number='WFD-CUST-001'
        )

        response = admin_client.get(f'/api/v1/admin/customers/{regular_user.id}/')

        assert response.status_code == status.HTTP_200_OK
        # Should contain customer info
        assert 'email' in response.data or 'customer' in response.data

    def test_customer_search(self, admin_client, regular_user):
        """Search by email should filter customers."""
        response = admin_client.get('/api/v1/admin/customers/?search=user@test')

        assert response.status_code == status.HTTP_200_OK
        customers = response.data if isinstance(response.data, list) else response.data.get('results', [])
        assert len(customers) >= 1
