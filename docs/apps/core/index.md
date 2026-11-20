# Core App

`apps/core` owns pages, revisions, content slots, title bindings, redirects, site
configuration and the write services. See the [project architecture](../../arch/project.md)
and [ADR index](../../arch/decisions/index.md).

## Models

| Model | Purpose |
| --- | --- |
| `Content` | Immutable canonical content, deduplicated by `(content_model, sha1)` |
| `Revision` | One edit; global `id` is the revid, `(page, page_rev_number)` unique |
| `RevisionSlot` | Named content role in a revision: `main` or `properties` |
| `Page` | Namespace, current revision, revision counter, redirect target, flags |
| `PageProtection` | Current structured protection per page/action with expiry |
| `ProtectionLog` | Append-only protection level change history |
| `TitleBinding` | Rebuildable title projection with release history |
| `SiteConfig` | Singleton for site name, anonymous read, site-level permissions |

A revision always has exactly two slots. Unchanged slots reuse the previous `Content`
row, so a property edit does not duplicate text and a text edit does not duplicate the
properties JSON.

## Services

| Module | Public functions |
| --- | --- |
| `services/content.py` | `canonicalize`, `get_or_create_content`, `validate_properties`, `default_properties` |
| `services/revisions.py` | `create_revision`, `get_revision_state`, `resolve_revision` |
| `services/pages.py` | `create_page`, `edit_page`, `delete_page`, `restore_page`, `protect_page`, `suppress_revision` |
| `services/titles.py` | `sync_title_bindings`, `resolve_title`, `rebuild_title_bindings` (title projection) |
| `services/titles.py` | `sync_title_bindings`, `resolve_title`, `rebuild_title_bindings` |
| `services/moves.py` | `move_page` (rename, redirect, swap) |

Every public service is atomic and permission-checked. `base_revid` is mandatory for
edits, moves, deletes, restores and protection changes.

`create_revision()` also calls the property app's `sync_category_bindings()` so titles
and categories are projected from the same properties object in one transaction.
Deleting a page releases both title and category bindings; restoring re-synchronizes
them and fails with `TitleConflict` if a title was taken.

## Structured protection

`PageProtection` has one row per `(page, action)` and a nullable `expires_at`.
`Page.protection_level(action)` returns the active level or `open`.
`ProtectionLog` records every level/expiry change with actor, reason and current
revision. `protect_page()` validates actions and levels, requires
`core.protect_page`, and updates rows + logs atomically. There is no free-form
`Page.protection` JSON field anymore.

## Titles and URLs

`properties.titles` is the source of truth:

```json
{"schema": 1, "titles": {"primary": "Main Page", "aliases": ["Home"]}}
```

- The primary title drives the canonical URL and heading.
- An alias resolves to the page; the web layer should 301 to the primary title.
- A redirect page is a regular `Page` with `redirect_target`; its title is bound
  normally.
- Removing or changing a title releases the binding; it is never deleted. Query
  `TitleBinding` for the complete history.
- Title normalization is Python-side: NFC, underscores/spaces, whitespace collapse,
  first-letter case, `casefold()` uniqueness key, 255-character/byte limit.

## Revision identity

- `Revision.id` — global revid, MediaWiki-compatible.
- `Revision.slug` — `p{page_id}-r{page_rev_number}` for readable permalinks.
- `Revision.parse_slug()` parses the slug; lookups verify both fields.

## Tests

```bash
uv run pytest apps/core/tests -q
```

Tests cover slot invariants, content deduplication, stale `base_revid` rollback,
titles/aliases and release history, moves/redirects/swaps, delete/restore, structured
protection and expiry, blocked editors, and rebuild idempotency.
