"""Tests for group permission seeding."""

import pytest
from django.contrib.auth.models import Group

from apps.user.groups import GROUP_PERMISSIONS, seed_groups

pytestmark = pytest.mark.django_db


def test_groups_have_configured_permissions():
    """Fresh migrations create every group with its full permission set."""
    for name, permissions in GROUP_PERMISSIONS.items():
        group = Group.objects.get(name=name)
        assert group.permissions.count() == len(permissions), name


def test_seeding_is_idempotent():
    """Rerunning the seeder does not duplicate or drop permissions."""
    first = seed_groups()
    second = seed_groups()
    assert first == second
    for name, permissions in GROUP_PERMISSIONS.items():
        assert Group.objects.get(name=name).permissions.count() == len(permissions)
