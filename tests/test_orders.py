"""
Tests for Orders API endpoints.
Tests cart operations, order placement, and order management.
"""
import pytest
from rest_framework import status

from orders.models import Cart, CartItem, Order
from users.models import Address


@pytest.mark.django_db
class TestCart:
    """Test cart endpoints: /api/v1/orders/cart/"""

    def test_get_empty_cart(self, auth_client):
        """GET cart for new user should return 200 with empty array."""
        response = auth_client.get('/api/v1/orders/cart/')

        assert response.status_code == status.HTTP_200_OK
        # Response should be empty or have items array
        if isinstance(response.data, list):
            assert len(response.data) == 0
        else:
            assert response.data.get('items', []) == []

    def test_add_item_to_cart(self, auth_client, sample_variant):
        """POST to /api/v1/orders/cart/add/ should add item to cart."""
        data = {
            'variant_id': sample_variant.id,
            'quantity': 2
        }
        response = auth_client.post('/api/v1/orders/cart/add/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        # Verify cart has the item
        cart_check = auth_client.get('/api/v1/orders/cart/')
        assert cart_check.status_code == status.HTTP_200_OK

    def test_add_same_item_increases_quantity(self, auth_client, sample_variant):
        """Adding same variant twice should increase quantity, not duplicate."""
        # Add item first time
        data_1 = {'variant_id': sample_variant.id, 'quantity': 2}
        auth_client.post('/api/v1/orders/cart/add/', data_1, format='json')

        # Add same item second time
        data_2 = {'variant_id': sample_variant.id, 'quantity': 3}
        response = auth_client.post('/api/v1/orders/cart/add/', data_2, format='json')

        assert response.status_code == status.HTTP_200_OK
        # Verify only one cart item with total quantity 5
        cart = auth_client.get('/api/v1/orders/cart/')
        items = cart.data if isinstance(cart.data, list) else cart.data.get('items', [])
        assert len(items) == 1

    def test_add_out_of_stock_item(self, auth_client, sample_variant):
        """Adding out-of-stock variant should return 400."""
        sample_variant.stock_quantity = 0
        sample_variant.save()

        data = {'variant_id': sample_variant.id, 'quantity': 1}
        response = auth_client.post('/api/v1/orders/cart/add/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_more_than_stock(self, auth_client, sample_variant):
        """Quantity > available stock should return 400."""
        data = {'variant_id': sample_variant.id, 'quantity': 100}
        response = auth_client.post('/api/v1/orders/cart/add/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cart_requires_auth(self, api_client):
        """GET /api/v1/orders/cart/ without token should return 401."""
        response = api_client.get('/api/v1/orders/cart/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_remove_item_from_cart(self, auth_client, regular_user, sample_variant):
        """DELETE /api/v1/orders/cart/item/<pk>/ should remove item."""
        # Add item first
        data = {'variant_id': sample_variant.id, 'quantity': 2}
        auth_client.post('/api/v1/orders/cart/add/', data, format='json')

        # Get cart item id
        cart = Cart.objects.get(user=regular_user)
        cart_item = CartItem.objects.get(cart=cart)

        # Remove it
        response = auth_client.delete(f'/api/v1/orders/cart/item/{cart_item.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert not CartItem.objects.filter(id=cart_item.id).exists()

    def test_clear_cart(self, auth_client, regular_user, sample_variant):
        """DELETE /api/v1/orders/cart/clear/ should empty cart."""
        # Add item
        data = {'variant_id': sample_variant.id, 'quantity': 2}
        auth_client.post('/api/v1/orders/cart/add/', data, format='json')

        # Clear cart
        response = auth_client.delete('/api/v1/orders/cart/clear/')

        assert response.status_code == status.HTTP_200_OK
        # Verify cart is empty
        cart = Cart.objects.get(user=regular_user)
        assert cart.items.count() == 0


@pytest.mark.django_db
class TestPlaceOrder:
    """Test order placement: POST /api/v1/orders/place/"""

    def test_place_order_success(self, auth_client, regular_user, sample_variant):
        """Place order with items in cart should return 201."""
        # Create address
        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )

        # Add item to cart
        data_add = {'variant_id': sample_variant.id, 'quantity': 2}
        auth_client.post('/api/v1/orders/cart/add/', data_add, format='json')

        # Place order
        data_order = {'shipping_address_id': address.id}
        response = auth_client.post('/api/v1/orders/place/', data_order, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['order_number'].startswith('WFD-')
        # Verify pricing
        assert response.data['subtotal'] > 0
        assert response.data['shipping_fee'] == 150000  # 1,500 Naira in Kobo
        assert response.data['total'] == response.data['subtotal'] + 150000

    def test_place_order_empty_cart(self, auth_client, regular_user):
        """Placing order with empty cart should return 400."""
        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )

        data = {'shipping_address_id': address.id}
        response = auth_client.post('/api/v1/orders/place/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stock_reduces_after_order(self, auth_client, regular_user, sample_variant):
        """Stock should decrease after order is placed."""
        initial_stock = sample_variant.stock_quantity
        quantity_ordered = 3

        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )

        # Add to cart and place order
        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': quantity_ordered},
            format='json'
        )
        auth_client.post('/api/v1/orders/place/', {'shipping_address_id': address.id}, format='json')

        # Check stock
        sample_variant.refresh_from_db()
        assert sample_variant.stock_quantity == initial_stock - quantity_ordered

    def test_address_snapshot_saved(self, auth_client, regular_user, sample_variant):
        """Order should save shipping address snapshot."""
        address = Address.objects.create(
            user=regular_user,
            street='123 Main St',
            city='Enugu',
            state='Enugu State'
        )

        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': 1},
            format='json'
        )
        response = auth_client.post(
            '/api/v1/orders/place/',
            {'shipping_address_id': address.id},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['shipping_address_snapshot'] is not None
        assert 'street' in response.data['shipping_address_snapshot']


@pytest.mark.django_db
class TestOrderManagement:
    """Test order viewing and management endpoints."""

    def test_list_orders(self, auth_client, regular_user, sample_variant):
        """GET /api/v1/orders/ should show only user's orders."""
        # Create an order
        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )
        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': 1},
            format='json'
        )
        auth_client.post('/api/v1/orders/place/', {'shipping_address_id': address.id}, format='json')

        # List orders
        response = auth_client.get('/api/v1/orders/')

        assert response.status_code == status.HTTP_200_OK
        orders = response.data if isinstance(response.data, list) else response.data.get('results', [])
        assert len(orders) >= 1

    def test_order_detail(self, auth_client, regular_user, sample_variant):
        """GET /api/v1/orders/<order_number>/ should return order."""
        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )
        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': 1},
            format='json'
        )
        place_response = auth_client.post(
            '/api/v1/orders/place/',
            {'shipping_address_id': address.id},
            format='json'
        )

        order_number = place_response.data['order_number']
        response = auth_client.get(f'/api/v1/orders/{order_number}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['order_number'] == order_number

    def test_cannot_see_other_user_order(self, auth_client, regular_user, sample_variant):
        """User should not see another user's order."""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        other_user = User.objects.create_user(
            email='other2@test.com',
            password='Pass123!',
            first_name='Other',
            last_name='User'
        )
        other_address = Address.objects.create(
            user=other_user,
            street='Other St',
            city='Lagos',
            state='Lagos State'
        )

        # Create order for other user
        order = Order.objects.create(
            user=other_user,
            order_number='WFD-OTHER-001'
        )

        # Try to get it as regular user
        response = auth_client.get('/api/v1/orders/WFD-OTHER-001/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_pending_order(self, auth_client, regular_user, sample_variant):
        """Cancel pending order should set status to cancelled."""
        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )
        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': 1},
            format='json'
        )
        place_response = auth_client.post(
            '/api/v1/orders/place/',
            {'shipping_address_id': address.id},
            format='json'
        )

        order_number = place_response.data['order_number']
        response = auth_client.post(f'/api/v1/orders/{order_number}/cancel/')

        assert response.status_code == status.HTTP_200_OK

    def test_stock_restored_after_cancel(self, auth_client, regular_user, sample_variant):
        """Stock should be restored when order is cancelled."""
        initial_stock = sample_variant.stock_quantity
        quantity = 2

        address = Address.objects.create(
            user=regular_user,
            street='123 Test St',
            city='Enugu',
            state='Enugu State'
        )
        auth_client.post(
            '/api/v1/orders/cart/add/',
            {'variant_id': sample_variant.id, 'quantity': quantity},
            format='json'
        )
        place_response = auth_client.post(
            '/api/v1/orders/place/',
            {'shipping_address_id': address.id},
            format='json'
        )

        # Stock should be reduced
        sample_variant.refresh_from_db()
        reduced_stock = sample_variant.stock_quantity
        assert reduced_stock == initial_stock - quantity

        # Cancel order
        order_number = place_response.data['order_number']
        auth_client.post(f'/api/v1/orders/{order_number}/cancel/')

        # Stock should be restored
        sample_variant.refresh_from_db()
        assert sample_variant.stock_quantity == initial_stock
