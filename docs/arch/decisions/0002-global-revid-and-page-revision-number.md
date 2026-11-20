# 0002 — Global revid and per-page revision number

- Status: Accepted
- Date: 2026-11-20

## Context

MediaWiki exposes a global numeric `revid` (`oldid`) and a `parentid`. External tools,
permalinks, recent changes and logs rely on it. The original project had two independent
auto-increment sequences, so no global revision identity existed.

## Decision

- `Revision.id` is a global `BigAutoField` and is the canonical `revid`, compatible with
  MediaWiki `oldid` lookups. Gaps are allowed.
- `Revision.page_rev_number` is a per-page sequence starting at 1, with
  `unique(page, page_rev_number)`.
- The public readable slug is `p{page_id}-r{page_rev_number}` (for example `p42-r7`).
  It is a routing alias, not a database key.
- Internal foreign keys always use `Revision.id`. The slug is parsed by the revision
  lookup layer and checked against the revision's actual page and number.

## Consequences

- API and URLs accept both `/api/v1/revisions/12345/` and `/api/v1/revisions/p42-r7/`.
- Logs and projections can reference one global revision ID.
- The per-page number gives short, human-readable permalinks while the global ID remains
  MediaWiki-compatible.
- `page_rev_number` is allocated under a row lock using `Page.revision_count`; the unique
  constraint is the concurrency backstop.

## Rejected alternatives

- `pageid-revid` as the primary key: larger keys, composite foreign keys, extra parsing,
  and it still does not provide global ordering.
- ULID/UUIDv7 primary key: modern and distributed-friendly, but breaks numeric `oldid`
  compatibility and makes indexes larger.
- Shared database sequence across two revision tables: not portable to SQLite.

## Follow-up

- Add `repair_revision_counters()` for imports and manual data repair.
