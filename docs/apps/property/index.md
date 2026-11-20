# Property App

The property app owns category projections. Titles live in the core `properties` slot
and are projected by `core.TitleBinding`; categories follow the same pattern.

## Source of truth

`properties.categories` is a list of category titles:

```json
{
  "schema": 1,
  "titles": {"primary": "Main Page", "aliases": []},
  "categories": ["Category:People", "Category:Stubs"]
}
```

Titles may be written with or without the `Category:` prefix. Normalization uses the
core title normalizer with namespace 14, so underscores, whitespace, Unicode and case
behave consistently with page titles. Categories in another namespace are rejected.

## `CategoryBinding`

- `page` FK, `namespace` (default 14), `display_title`, `normalized_title`
- `created_revision`, `released_revision`, `created_at`, `released_at`
- partial unique active `(page, namespace, normalized_title)`
- indexes on `(namespace, normalized_title, released_at)` and `(page, released_at)`

Rows are never physically deleted. Removing a category releases its binding; the
former page association remains queryable. Multiple pages may belong to the same
category, so uniqueness is per page/category, not global.

## Services

- `sync_category_bindings(page, revision, properties)` — called by
  `core.services.revisions.create_revision` inside the revision transaction.
- `rebuild_category_bindings(check_only=False)` — reconciles every live page from its
  current revision.

Management command:

```bash
uv run python manage.py rebuild_category_bindings --check
uv run python manage.py rebuild_category_bindings
```

Soft-deleting a page releases its category bindings; restoring resynchronizes them.

## Removed legacy models

The old `Category` and `CategoryLog` tables (raw integer IDs, no foreign keys) were
removed and their migration reset. Do not reintroduce a second category source of
truth.

## Tests

```bash
uv run pytest apps/property/tests -q
```
