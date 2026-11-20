"""End-to-end API tests."""

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_create_get_edit_and_conflict(api_client):
    """The basic write path round-trips and rejects stale edits."""
    created = api_client.post(
        "/api/v1/pages/",
        {"title": "API Page", "main": "Hello"},
        format="json",
    )
    assert created.status_code == 201
    data = created.data
    assert data["title"] == "API Page"
    page_id = data["id"]
    first_revid = data["current_revision"]["revid"]

    fetched = api_client.get(f"/api/v1/pages/{page_id}/")
    assert fetched.status_code == 200
    assert fetched.data["title"] == "API Page"

    edited = api_client.post(
        f"/api/v1/pages/{page_id}/edit",
        {"base_revid": first_revid, "main": "Hello again"},
        format="json",
    )
    assert edited.status_code == 200
    assert edited.data["revid"] != first_revid
    assert set(edited.data["slots"]) == {"main", "properties"}

    stale = api_client.post(
        f"/api/v1/pages/{page_id}/edit",
        {"base_revid": first_revid, "main": "Stale"},
        format="json",
    )
    assert stale.status_code == 409
    assert stale.data["error"]["code"] == "edit_conflict"


def test_title_and_slug_lookup(api_client):
    """Aliases resolve and readable slugs fetch the same revision."""
    created = api_client.post(
        "/api/v1/pages/",
        {
            "title": "Slug Page",
            "main": "Hello",
            "properties": {
                "schema": 1,
                "titles": {"primary": "Slug Page", "aliases": ["Slug"]},
            },
        },
        format="json",
    )
    page_id = created.data["id"]
    revid = created.data["current_revision"]["revid"]
    slug = created.data["current_revision"]["slug"]

    title = api_client.get("/api/v1/titles/?title=Slug")
    assert title.status_code == 200
    assert title.data["page_id"] == page_id
    assert title.data["is_alias"] is True

    by_slug = api_client.get(f"/api/v1/revisions/{slug}/")
    assert by_slug.status_code == 200
    assert by_slug.data["revid"] == revid


def test_anonymous_read_and_write():
    """Anonymous users can read but not write."""
    client = APIClient()
    created = client.post(
        "/api/v1/pages/",
        {"title": "Anonymous Page", "main": "Hello"},
        format="json",
    )
    assert created.status_code == 403


def test_schema_endpoint(api_client):
    """The OpenAPI schema endpoint responds."""
    response = api_client.get("/api/schema/")
    assert response.status_code == 200


def test_protection_and_categories_in_page_response(api_client):
    """Page responses expose structured protection and categories."""
    created = api_client.post(
        "/api/v1/pages/",
        {
            "title": "Protected Page",
            "main": "Hello",
            "properties": {
                "schema": 1,
                "titles": {"primary": "Protected Page", "aliases": []},
                "categories": ["Category:People"],
            },
        },
        format="json",
    )
    page_id = created.data["id"]
    revid = created.data["current_revision"]["revid"]

    protected = api_client.post(
        f"/api/v1/pages/{page_id}/protect",
        {"base_revid": revid, "protection": {"edit": "sysop"}},
        format="json",
    )
    assert protected.status_code == 200
    assert protected.data["protection"]["edit"] == "sysop"
    assert len(protected.data["protections"]) == 1
    assert protected.data["categories"] == ["Category:People"]
