"""
Pytest configuration and fixtures for all tests.
"""
import pytest
import os
from django.contrib.auth import get_user_model
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, Product, ProductVariant
from orders.models import Cart

User = get_user_model()

# Configure pytest-django to use transactional strategy
pytest_plugins = 'pytest_django'


@pytest.fixture(scope='session', autouse=True)
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup Django database for tests using transactional rollback."""
    with django_db_blocker.unblock():
        call_command('migrate', '--run-syncdb', verbosity=0)


@pytest.fixture
def api_client():
    """Return an APIClient instance."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return a superuser/staff user for testing."""
    user = User.objects.create_superuser(
        email='admin@test.com',
        password='Admin2025!',
        first_name='Admin',
        last_name='User'
    )
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def regular_user(db):
    """Create and return a regular (non-staff) user for testing."""
    return User.objects.create_user(
        email='user@test.com',
        password='User2025!',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_token(db, admin_user):
    """Return access token for admin user."""
    refresh = RefreshToken.for_user(admin_user)
    return str(refresh.access_token)


@pytest.fixture
def user_token(db, regular_user):
    """Return access token for regular user."""
    refresh = RefreshToken.for_user(regular_user)
    return str(refresh.access_token)


@pytest.fixture
def auth_client(api_client, user_token):
    """Return APIClient with regular user token in Authorization header."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
    return api_client


@pytest.fixture
def admin_client(api_client, admin_token):
    """Return APIClient with admin token in Authorization header."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    return api_client


@pytest.fixture
def sample_category(db):
    """Create and return a sample product category."""
    return Category.objects.create(
        name='Test Tees',
        slug='test-tees'
    )


@pytest.fixture
def sample_product(db, sample_category):
    """Create and return a sample product."""
    return Product.objects.create(
        name='Test Tee',
        slug='test-tee',
        description='A test product',
        price=1200000,  # 12,000 Naira in Kobo
        category=sample_category,
        is_active=True,
        is_featured=False
    )


@pytest.fixture
def sample_variant(db, sample_product):
    """Create and return a sample product variant."""
    return ProductVariant.objects.create(
        product=sample_product,
        size='M',
        colour='Black',
        sku='TEST-TEE-M-BLK',
        stock_quantity=10
    )
