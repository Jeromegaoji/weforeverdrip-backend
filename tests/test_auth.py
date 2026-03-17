"""
Tests for Users & Authentication API endpoints.
Tests registration, login, profiles, logout, and address management.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test POST /api/v1/auth/register/ endpoint."""

    def test_register_success(self, api_client):
        """Register with valid data should return 201 with tokens."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert User.objects.filter(email='newuser@test.com').exists()

    def test_register_duplicate_email(self, api_client):
        """Registering with duplicate email should return 400."""
        # Create first user
        User.objects.create_user(
            email='duplicate@test.com',
            password='Pass123!',
            first_name='Test',
            last_name='User'
        )
        # Try to register with same email
        data = {
            'email': 'duplicate@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!'
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_password_mismatch(self, api_client):
        """Password and confirm_password mismatch should return 400."""
        data = {
            'email': 'newuser@test.com',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!'
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password(self, api_client):
        """Password less than 8 characters should return 400."""
        data = {
            'email': 'newuser@test.com',
            'password': 'Short1!',
            'confirm_password': 'Short1!'
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Test POST /api/v1/auth/login/ endpoint."""

    def test_login_success(self, api_client, regular_user):
        """Login with correct credentials should return 200 with token."""
        data = {
            'email': 'user@test.com',
            'password': 'User2025!'
        }
        response = api_client.post('/api/v1/auth/login/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_login_wrong_password(self, api_client, regular_user):
        """Login with wrong password should return 400."""
        data = {
            'email': 'user@test.com',
            'password': 'WrongPassword'
        }
        response = api_client.post('/api/v1/auth/login/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_email(self, api_client):
        """Login with non-existent email should return 400."""
        data = {
            'email': 'nonexistent@test.com',
            'password': 'AnyPassword123!'
        }
        response = api_client.post('/api/v1/auth/login/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfile:
    """Test GET/PATCH /api/v1/auth/profile/ endpoint."""

    def test_get_profile_authenticated(self, auth_client, regular_user):
        """Get profile as authenticated user should return 200."""
        response = auth_client.get('/api/v1/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'user@test.com'

    def test_get_profile_unauthenticated(self, api_client):
        """Get profile without token should return 401."""
        response = api_client.get('/api/v1/auth/profile/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, auth_client, regular_user):
        """Update profile as authenticated user should return 200."""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = auth_client.patch('/api/v1/auth/profile/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        # Verify update persisted
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'Updated'
        assert regular_user.last_name == 'Name'


@pytest.mark.django_db
class TestLogout:
    """Test POST /api/v1/auth/logout/ endpoint."""

    def test_logout_success(self, auth_client, user_token):
        """Logout with valid refresh token should return 200."""
        # Get token info to extract refresh token
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(email='user@test.com')
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        # Logout with access token in header and refresh in body
        logout_response = auth_client.post(
            '/api/v1/auth/logout/',
            {'refresh': refresh_token},
            format='json'
        )

        assert logout_response.status_code == status.HTTP_200_OK

    def test_logout_blacklisted_token(self, auth_client):
        """Using refresh token after logout should return 401."""
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(email='user@test.com')
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)

        # Logout (blacklist token)
        auth_client.post(
            '/api/v1/auth/logout/',
            {'refresh': refresh_token},
            format='json'
        )

        # Try to use blacklisted refresh token
        api_client = APIClient()
        refresh_response = api_client.post(
            '/api/v1/auth/token/refresh/',
            {'refresh': refresh_token},
            format='json'
        )

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAddresses:
    """Test address CRUD endpoints under /api/v1/auth/addresses/"""

    def test_create_address(self, auth_client, regular_user):
        """Create address should return 201 and link to user."""
        data = {
            'street': '123 Main Street',
            'city': 'Enugu',
            'state': 'Enugu State',
            'country': 'Nigeria'
        }
        response = auth_client.post('/api/v1/auth/addresses/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['street'] == '123 Main Street'
        # Verify address linked to current user
        assert regular_user.addresses.count() == 1

    def test_list_addresses(self, auth_client, regular_user):
        """List addresses should show only current user's addresses."""
        # Create 2 addresses for current user
        from users.models import Address
        Address.objects.create(
            user=regular_user,
            street='First Street',
            city='Enugu',
            state='Enugu State'
        )
        Address.objects.create(
            user=regular_user,
            street='Second Street',
            city='Lagos',
            state='Lagos State'
        )

        response = auth_client.get('/api/v1/auth/addresses/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_cannot_access_other_user_address(self, auth_client, regular_user):
        """User should not be able to access another user's address."""
        from users.models import Address
        other_user = User.objects.create_user(
            email='other@test.com',
            password='Pass123!',
            first_name='Other',
            last_name='User'
        )
        other_address = Address.objects.create(
            user=other_user,
            street='Other Street',
            city='Abuja',
            state='FCT'
        )

        response = auth_client.get(f'/api/v1/auth/addresses/{other_address.id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_address(self, auth_client, regular_user):
        """Delete address should return 204."""
        from users.models import Address
        address = Address.objects.create(
            user=regular_user,
            street='To Delete',
            city='Enugu',
            state='Enugu State'
        )

        response = auth_client.delete(f'/api/v1/auth/addresses/{address.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Address.objects.filter(id=address.id).exists()
