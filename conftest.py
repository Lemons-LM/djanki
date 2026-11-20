"""Shared pytest fixtures."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.core.services.pages import create_page

User = get_user_model()


@pytest.fixture
def user(db):
    """Return a superuser for service-level tests."""
    return User.objects.create_user(
        username="alice",
        password="test-password",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def page(user):
    """Create a page with a primary title and no aliases."""
    return create_page(title="Main Page", main_content="Hello", author=user)


@pytest.fixture
def api_client(user):
    """Return an authenticated DRF client."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client
