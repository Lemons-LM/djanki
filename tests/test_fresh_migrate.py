"""Fresh-database invariants that are easy to break in migrations."""

import pytest
from django.contrib.auth.models import Group

from apps.core.models.site import SiteConfig
from apps.user.groups import GROUP_PERMISSIONS

pytestmark = pytest.mark.django_db


def test_site_config_singleton_exists():
    """The seed migration creates the singleton row."""
    assert SiteConfig.objects.filter(pk=1).exists()


def test_groups_match_configuration():
    """The post-migrate receiver creates groups with exact permission counts."""
    for name, permissions in GROUP_PERMISSIONS.items():
        assert Group.objects.get(name=name).permissions.count() == len(permissions)
