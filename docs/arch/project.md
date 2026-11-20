# Project Architecture

This document describes the current core architecture. The detailed decisions are in
the [ADR index](decisions/index.md).

## Goals

Djanki is a MediaWiki rewrite in Django. The design aims to keep MediaWiki semantics
at the edges while using a cleaner internal model:

- Python instead of PHP.
- Everything is content/property, including titles.
- MediaWiki tools remain usable through a compatibility adapter.
- A versioned REST API instead of `api.php?action=...`.

## Core model

```
Page
  current_revision ──► Revision ──► RevisionSlot ──► Content
  namespace            id (revid)     role=main       content_model
  revision_count       page_rev_number role=properties data (canonical text)
  redirect_target      parent_revision                 sha1 (dedup key)
  is_deleted           author / timestamps             size
  is_suppressed        comment / flags
        │
        ├── TitleBinding (projection)
        │     page, namespace, display_title, normalized_title
        │     is_primary, created_revision, released_revision
        │
        ├── CategoryBinding (projection, property app)
        │     page, namespace, display_title, normalized_title
        │     created_revision, released_revision
        │
        ├── PageProtection (current level per action, expiry)
        └── ProtectionLog (append-only changes)

user.WikiUser ──► user.Block (history, expiry, lift fields)
```

- `Content` is immutable and content-addressed by `(content_model, sha1)`.
- `Revision` is one edit and carries a complete page snapshot as slots.
- Every revision has exactly one `main` and one `properties` slot.
- `Page.current_revision` is the only current-state pointer.
- `TitleBinding` and `CategoryBinding` are rebuildable projections; rows are released,
  never physically deleted.
- `PageProtection` stores the current structured level per action; `ProtectionLog`
  records every change.
- `Block` is append-only block history; active state is derived from time and lift
  fields.
- `SiteConfig` is a singleton hosting site-level rights and the anonymous-read flag.

## Write path

```
API view / admin action
    └── service (transaction.atomic + permission check + base_revid check)
          ├── Content.get_or_create (canonicalize + SHA-1 dedup)
          ├── Revision + two RevisionSlots
          ├── Page.current_revision / revision_count update
          └── title binding diff (release removed, create new)
```

All writes go through `apps/core/services/`; signals do not write domain state.

## Read path

```
title ─► normalize ─► active TitleBinding ─► Page
                    └─► redirect_target / alias ─► canonical primary binding
revid or p{page_id}-r{n} ─► Revision ─► slots ─► Content
```

## Invariants

1. Every revision has exactly `main` and `properties` slots (service-enforced).
2. Every non-deleted page has exactly one active primary title.
3. At most one page actively owns a `(namespace, normalized_title)` key.
4. Title binding rows are never deleted; release sets `released_at`.
5. A revision is complete: unchanged slots reuse existing `Content` objects.
6. `Revision.id` is the global revid; `(page, page_rev_number)` is unique per page.
7. Mutations require `base_revid`; a mismatch raises `EditConflict` and rolls back.
8. All writes are atomic and permission-checked in the service layer.

## Module map

| Path | Responsibility |
| --- | --- |
| `apps/core/models/` | `Content`, `Revision`, `RevisionSlot`, `Page`, `TitleBinding`, `SiteConfig` |
| `apps/core/services/content.py` | Canonicalization, SHA-1 dedup, property validation |
| `apps/core/services/revisions.py` | Revision creation, slot invariants, revid lookup |
| `apps/core/services/pages.py` | Create/edit/delete/restore/protect/suppress |
| `apps/core/services/titles.py` | Title sync, resolution, rebuild |
| `apps/core/services/moves.py` | Rename, swap, redirect |
| `apps/core/titles.py` | Python-side title normalization |
| `apps/core/permissions.py` | Global + object-level `can()` / `require()` |
| `apps/core/selectors.py` | Read helpers and pagination |
| `apps/api/` | DRF serializers, views, URL routing and error envelope |
| `apps/user/groups.py` | Group matrix and `post_migrate` seeding |
| `apps/user/services/blocks.py` | Block/unblock services |
| `apps/property/` | `CategoryBinding` projection service and model |

## Current scope

Implemented: core model and services, title and category projections, redirects,
structured protection and protection logs, block history and expiry, permission groups
and object checks, REST API, admin read-only views, SQLite/PostgreSQL CI, mypy, tests
and fresh-database verification.

Not yet implemented: web UI, parser, search, file upload/storage, full MediaWiki action
API adapter, IP/range blocks, cascading protection, category pages/member listings.
