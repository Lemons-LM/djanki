# 0010 — Category binding projection

- Status: Accepted
- Date: 2026-11-20

## Context

The property app contained legacy `Category` and `CategoryLog` tables using raw
`page_id` / `category_id` integers. They were not foreign keys, were not integrated
with the unified revision model, and the log write methods were broken. Categories are
part of the page properties, so the legacy tables duplicated the source of truth.

## Decision

Replace the legacy tables with `property.CategoryBinding`:

- `page` FK, `namespace` (default category namespace 14), `display_title`,
  `normalized_title`
- `created_revision`, `released_revision`, `created_at`, `released_at`
- Partial unique active `(page, namespace, normalized_title)`
- Rows are released, never deleted, so membership history remains queryable

`properties.categories` is a list of category titles. `sync_category_bindings()` runs
inside `create_revision()` and reconciles active rows. Multiple pages may share a
category, so uniqueness is per page/category, not global. `rebuild_category_bindings`
and a management command rebuild the projection from current revisions.

## Consequences

- Categories are now derived from the same revision/properties source as titles.
- Removing a category releases its binding and keeps history.
- Soft-deleting a page releases its category bindings; restore resynchronizes them.
- The legacy `Category`/`CategoryLog` tables and their migration are removed.

## Rejected alternatives

- Keep independent category tables and synchronize them manually: two sources of truth.
- Store category membership only in JSON and query it directly: no portable indexes.
- Make categories a global unique relation: wrong; many pages share a category.

## Follow-up

- Category pages and member listings (query the projection).
- Category rename/move semantics.
- Rebuild command scheduling after bulk imports.
