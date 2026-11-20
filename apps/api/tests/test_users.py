"""API tests for block and unblock endpoints."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.user.models import Block

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_block_and_unblock(api_client):
    """A sysop can block, inspect history and unblock through the API."""
    target = User.objects.create_user(username="target", password="test-password")

    blocked = api_client.post(
        f"/api/v1/users/{target.pk}/block",
        {"reason": "vandalism"},
        format="json",
    )
    assert blocked.status_code == 201
    assert blocked.data["is_active"] is True
    assert Block.active_for(target).exists()

    history = api_client.get(f"/api/v1/users/{target.pk}/blocks/")
    assert history.status_code == 200
    assert history.data["count"] == 1

    unblocked = api_client.post(
        f"/api/v1/users/{target.pk}/unblock",
        {"reason": "appeal"},
        format="json",
    )
    assert unblocked.status_code == 200
    assert unblocked.data["unblocked"] == 1
    target.refresh_from_db()
    assert target.is_currently_blocked is False


def test_block_requires_permission():
    """A user without block rights receives 403."""
    editor = User.objects.create_user(username="editor", password="test-password")
    editor.groups.add(Group.objects.get(name="user"))
    target = User.objects.create_user(username="target", password="test-password")
    client = APIClient()
    client.force_authenticate(user=editor)

    response = client.post(
        f"/api/v1/users/{target.pk}/block",
        {"reason": "nope"},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"
