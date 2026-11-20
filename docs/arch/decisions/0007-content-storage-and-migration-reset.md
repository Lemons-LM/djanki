# 0007 — Content storage and migration reset

- Status: Accepted
- Date: 2026-11-20

## Context

Content must be immutable, hashable and portable across SQLite (development) and
PostgreSQL (production). JSON properties also need deterministic hashing for deduplication,
which is awkward if the database normalises `jsonb` keys differently. The repository has
no production data, and the existing migrations encode an incompatible model with circular
non-null foreign keys.

## Decision

- Store content in `Content.data` as `TextField`:
  - text models: the raw string;
  - JSON: canonical JSON text with `ensure_ascii=False`, `sort_keys=True`,
    compact separators and `allow_nan=False`.
- `Content.sha1` is the SHA-1 of the UTF-8 bytes; `Content.size` is the byte length.
- Unique `(content_model, sha1)` provides deduplication. `get_or_create_content()` verifies
  that an existing row's data matches and raises `ContentHashCollision` otherwise.
- Property queries use projections (`TitleBinding`, later `CategoryBinding`) rather than
  ad-hoc JSON lookups, keeping SQLite and PostgreSQL behaviour identical.

## Migration reset

Because there is no real data:

- Delete `core/migrations/0001_initial.py` and `0002_initial.py`.
- Delete `user/migrations/0002_auto_20260410_1706.py` and `0003_alter_wikiuser_options.py`.
- Keep `user/0001_initial.py`; regenerate user options after the permission change.
- Generate fresh `core/0001`, `file/0001` and `property/0001`.
- Seed `SiteConfig` in a small data migration; seed groups in `post_migrate`, never in a
  migration.

Local developers must delete their development database and run `migrate` again. Do not
use `--fake`. `DJANGO_DB_PATH` can point SQLite at a temporary file for fresh-migration
tests and CI.

## Consequences

- Deterministic deduplication across backends.
- SHA-1 matches MediaWiki metadata and is cheap; a collision is detected rather than
  silently corrupting content.
- JSON is not directly queryable with ORM key lookups; projections are the supported path.
- Migration reset intentionally breaks existing local databases.

## Rejected alternatives

- `JSONField` for property content: backend-dependent normalisation and harder hashing.
- Incremental `RemoveField`/`AddField` migrations: more complex and pointless without data.
- SHA-256 only: stronger, but MediaWiki compatibility favours SHA-1; can be added later.

## Follow-up

- Add unreferenced `Content` garbage collection.
- Consider storing SHA-256 alongside SHA-1 for defence in depth.
