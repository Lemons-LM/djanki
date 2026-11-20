# Testing

## Configuration

`pyproject.toml` configures pytest-django:

- `DJANGO_SETTINGS_MODULE = "config.settings.dev"` (SQLite, `DEBUG=True`)
- `python_files = ["tests.py", "test_*.py"]`
- `testpaths = ["apps", "tests"]`
- `addopts = "-ra"`

Test modules live in per-app packages:

```
apps/core/tests/
apps/user/tests/
apps/property/tests/
apps/api/tests/
tests/ test_fresh_migrate.py
conftest.py
```

## Commands

```bash
uv run pytest -q
uv run pytest apps/core/tests -q
uv run pytest apps/core/tests/test_pages.py -q
uv run pytest apps/core/tests/test_pages.py::test_create_page_creates_two_slots_and_primary_binding -q
uv run pytest -k "title" -q
```

Run the PostgreSQL path locally when a database is available:

```bash
DB_NAME=djanki DB_USER=djanki DB_PASSWORD=djanki \
uv run pytest -q --ds=config.settings.test
```

## Fixtures

`conftest.py` provides:

- `user` — a superuser for service-level tests
- `page` — a page created through `create_page` with a primary title
- `api_client` — an authenticated DRF `APIClient`

Add fixtures only when they are shared across apps. Keep app-specific helpers in the
app's `tests/` package.

## Writing tests

Prefer the public service layer:

```python
from apps.core.services.pages import create_page, edit_page

page = create_page(title="Main Page", main_content="Hello", author=user)
revision = edit_page(
    page_id=page.pk,
    author=user,
    base_revid=page.current_revision_id,
    main="Hello again",
)
```

Create rows directly only when testing model constraints, invalid states, or
projections that services normally maintain.

Assert invariants, not just status codes:

- every revision has `main` and `properties` slots;
- exactly one active primary `TitleBinding` per page;
- removed title/category rows are released, not deleted;
- stale `base_revid` raises `EditConflict` and leaves the page unchanged;
- blocked users cannot write but can read;
- expired protection no longer applies.

Use `pytest.raises` for domain exceptions (`EditConflict`, `TitleConflict`,
`PermissionDenied`, `InvalidBlock`). API tests should assert the error envelope:

```python
assert response.status_code == 409
assert response.data["error"]["code"] == "edit_conflict"
```

## Fresh-database tests

`tests/test_fresh_migrate.py` verifies that migrations create the `SiteConfig`
singleton and that `post_migrate` seeds every group with the configured permission
count. Add a test here when a migration or seeding change could break a fresh install.

To inspect a disposable database manually:

```bash
rm -f /tmp/djanki-fresh.sqlite3
DJANGO_DB_PATH=/tmp/djanki-fresh.sqlite3 uv run python manage.py migrate
DJANGO_DB_PATH=/tmp/djanki-fresh.sqlite3 uv run python manage.py shell -c \
  "from django.contrib.auth.models import Group; print({g.name: g.permissions.count() for g in Group.objects.all()})"
```

Expected: `user: 3`, `autoconfirmed: 5`, `sysop: 9`, `interface-admin: 3`, `bot: 3`,
`suppress: 2`, `bureaucrat: 2`.

## Performance checks

History and binding endpoints are paginated. When adding a list endpoint, use
selectors with `select_related` / `prefetch_related` and consider
`django_assert_num_queries` to prevent N+1 regressions.
