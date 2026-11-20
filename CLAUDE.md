# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Djanki is a MediaWiki rewrite in Django (Python >=3.12, Django >=6.0.3, GPL-3.0). The architectural goals, from `docs/arch/new_arch.md`:

1. Python instead of PHP.
2. Everything is a property — including page titles — so it can be updated uniformly.
3. MediaWiki tools/functions should remain usable on Djanki.
4. RESTful API instead of `api.php?action=...`.

`core`, `user` and the API are implemented. `webui`, `parser`, `search`, file upload/storage and the MediaWiki action API adapter are still placeholders or partial.

## Commands

Dependencies are locked with `uv` (`uv.lock`).

```bash
uv sync --extra dev                 # install runtime + dev deps
uv run python manage.py runserver   # defaults to config.settings.dev
uv run python manage.py migrate
uv run python manage.py makemigrations
uv run python manage.py seed_groups  # idempotent group/permission seeding
uv run python manage.py rebuild_title_bindings --check
uv run python manage.py rebuild_category_bindings --check
uv run python manage.py shell

uv run pytest                                    # all tests
uv run pytest apps/core/tests -q                 # one app
uv run pytest apps/core/tests/test_pages.py -q   # one file
uv run pytest apps/core/tests/test_pages.py::test_create_page_creates_two_slots_and_primary_binding -q
uv run pytest -k "title" -q                      # by name

uv run ruff check .                 # lint (line-length 100)
uv run black .                      # format (line-length 100)
uv run mypy apps config             # type check
uv run pre-commit run --all-files   # local hooks
```

Fresh-database verification (use a temporary path, not your dev database):

```bash
rm -f /tmp/djanki-fresh.sqlite3
DJANGO_DB_PATH=/tmp/djanki-fresh.sqlite3 uv run python manage.py migrate --noinput
DJANGO_DB_PATH=/tmp/djanki-fresh.sqlite3 uv run python manage.py shell -c \
  "from django.contrib.auth.models import Group; print({g.name: g.permissions.count() for g in Group.objects.all()})"
```

Expected group counts: `user: 3`, `autoconfirmed: 5`, `sysop: 9`, `interface-admin: 3`, `bot: 3`, `suppress: 2`, `bureaucrat: 2`.

## Settings

Split in `config/settings/`:

- `base.py` — shared settings, SQLite (`DJANGO_DB_PATH` override), `AUTH_USER_MODEL = 'user.WikiUser'`, `DEFAULT_AUTO_FIELD`, DRF + drf-spectacular, `REST_FRAMEWORK` and `SPECTACULAR_SETTINGS`.
- `dev.py` — `DEBUG=True`; this is what `manage.py` loads by default and what pytest uses.
- `test.py` — PostgreSQL settings for CI (`DB_*` env vars, no SSL redirect).
- `prod.py` — PostgreSQL; requires env vars `DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, optionally `DB_HOST`/`DB_PORT`; required values use `os.environ[...]` so startup fails fast; enforces HTTPS/secure cookies and `X_FRAME_OPTIONS="DENY"`.

Run a one-off command against another settings module with `DJANGO_SETTINGS_MODULE=config.settings.prod ...`.

## Architecture

### App layout

Apps live under `apps/<name>` and are registered as `apps.<name>` in `INSTALLED_APPS`, so their Django app labels are the short names (`core`, `user`, `property`, ...). Each app follows the same package shape: `models/`, `views/`, `migrations/`, plus `apps.py`, `admin.py`, and a `tests/` package (or `tests.py`).

Domain responsibilities (from `docs/arch/apps.md`):

| App | Responsibility |
| --- | --- |
| `core` | Pages, revisions, slots, titles, redirects, protection, permissions, services |
| `user` | Users, groups, permissions, block history, login/logout |
| `api` | DRF REST API and future MediaWiki compatibility adapter |
| `webui` | Browser-facing presentation (not implemented) |
| `parser` | Djanki wikitext parser (not implemented) |
| `search` | Search (not implemented) |
| `special` | Special pages / wiki management (not implemented) |
| `file` | File metadata + permissions; upload/storage not implemented |
| `property` | `CategoryBinding` projection and rebuild services |
| `extension` | Extension/hook system (not implemented) |
| `template` | Template-related functions (not implemented) |

`common/` and `infrastructure/` are empty placeholder packages at the repository root.

### Core content model

One edit = one complete page snapshot:

- `Content` — immutable content blob. `data` is canonical text (raw text for text models, canonical JSON for JSON), `sha1` is the dedup key, and `(content_model, sha1)` is unique.
- `Revision` — one edit. `id` is the global MediaWiki-compatible revid; `page_rev_number` is the per-page sequence; `slug` is `p{page_id}-r{number}`.
- `RevisionSlot` — a named role in a revision: `main` or `properties`. Every revision has exactly one of each; the service enforces this.
- `Page` — namespace, `current_revision`, `revision_count`, `redirect_target`, deletion/suppression flags. There is no `current_title`, `current_property_revision` or protection JSON.
- `PageProtection` — current structured level per `(page, action)` with optional expiry.
- `ProtectionLog` — append-only protection level/expiry changes.
- `TitleBinding` — rebuildable projection of `properties.titles` with release history. Rows are never deleted; active means `released_at IS NULL`.
- `property.CategoryBinding` — the same projection pattern for `properties.categories`.
- `SiteConfig` — singleton hosting site-level permissions and `anonymous_read`.

Read path: title → normalized key → active `TitleBinding` → page → redirect/alias resolution. Revision path: revid or slug → revision → slots → content.

### Services and write path

All writes go through `apps/core/services/` inside `transaction.atomic()`; signals do not write domain state.

- `content.py` — canonicalization, SHA-1 dedup, property validation.
- `revisions.py` — `create_revision`, `get_revision_state`, `resolve_revision`.
- `pages.py` — `create_page`, `edit_page`, `delete_page`, `restore_page`, `protect_page`, `suppress_revision`.
- `titles.py` — `sync_title_bindings`, `resolve_title`, `rebuild_title_bindings`.
- `moves.py` — `move_page` (rename, redirect, swap).
- `apps/property/services/categories.py` — `sync_category_bindings`, `rebuild_category_bindings` (called by `create_revision`).

Edits, moves, deletes, restores and protection changes require `base_revid`; a mismatch raises `EditConflict` and rolls back. Unchanged slots reuse the current `Content` row, so property edits do not duplicate text.

### Titles

Titles live in the `properties` slot:

```json
{"schema": 1, "titles": {"primary": "Main Page", "aliases": ["Home"]}}
```

- Primary drives the canonical URL and heading; aliases resolve and should 301 to the primary.
- Removing an alias releases its `TitleBinding`; history remains queryable.
- Ordinary edits never steal an active title; use `move_page` for rename/swap.
- Normalization is Python-side in `apps/core/titles.py`: NFC, underscore/space folding, whitespace collapse, first-letter case, `casefold()` uniqueness key, 255-char/byte limit.

### Protection and blocks

- `PageProtection` has one row per `(page, action)`; `expires_at=None` means indefinite. `Page.protection_level(action)` returns the active level or `open`.
- `protect_page()` validates actions/levels, requires `core.protect_page`, checks `base_revid`, updates rows and appends `ProtectionLog` entries atomically.
- `user.Block` is append-only history: target, issuer, reason, start/expiry, lift fields, autoblock/no-create. `Block.active_for(user)` derives active state; `WikiUser.is_currently_blocked` uses it.
- `block_user()` / `unblock_user()` require `user.block_user` / `user.unblock_user`; blocking yourself, a deleted user, or with a past expiry raises `InvalidBlock`.
- API: `POST /api/v1/users/{id}/block`, `/unblock`, `GET /api/v1/users/{id}/blocks/`.

### Permissions and groups

Permissions are attached to the model they govern:

| Model | Permissions |
| --- | --- |
| `core.SiteConfig` | `read`, `edit_interface`, `edit_content_model`, `import_data`, `export_data` |
| `core.Page` | `edit_page`, `move_page`, `protect_page`, `suppress_page` |
| `file.File` | `upload_file`, `move_file` |
| `user.WikiUser` | `block_user`, `unblock_user`, `change_user_rights`, `send_email`, `bot` |

Django's built-in `delete_page`/`delete_file`/`view_*` permissions are also used. `apps/user/groups.py` seeds groups via a `post_migrate` receiver and the `seed_groups` command. Never seed groups from a migration.

Object-level checks live in `apps/core/permissions.py` (`can()` / `require()`), combining global permissions, account state, blocks, page protection and `SiteConfig.anonymous_read`. Services call `require()`; DRF permission classes call `can()` for early rejection.

### API

- DRF with `/api/v1/`, `/api/schema/`, `/api/docs/`.
- Session + token authentication; anonymous reads follow `SiteConfig.anonymous_read`.
- Error envelope: `{"error": {"code", "message", "details"}}`.
- `base_revid` is mandatory for mutations; conflicts return `409`.
- See `docs/apps/api/index.md` for endpoints.

### Property categories

Categories are a rebuildable projection of `properties.categories` (a list of category
titles). `CategoryBinding` keeps release history and allows many pages per category.
`sync_category_bindings` runs inside `create_revision`; deleting a page releases
bindings and restoring resynchronizes them. Rebuild with
`uv run python manage.py rebuild_category_bindings [--check]`.

The old `Category`/`CategoryLog` raw-ID tables were removed.

## Conventions

- **Architecture docs are mandatory.** `docs/index.md` states: any code you write must be documented in the matching file under `docs/` (arch in `docs/arch/`, per-app in `docs/apps/<app>/index.md`, routes in `docs/routes/index.md`), and every function must have a docstring. Treat this as a hard repo rule, not a suggestion.
- ADRs live in `docs/arch/decisions/`; add one for material architecture changes.
- `docs/arch/apps.md` is the canonical app-responsibility map; keep it current.
- `README.md` only points at `docs/`; put substantive documentation there.
- Formatting/lint is ruff + black at line length 100. Migrations are generated by Django and also formatted.
- **Type safety is enforced.** `mypy apps config` must pass (django-stubs + DRF stubs). Annotate public services, narrow nullable model pointers with local variables, and add targeted `# type: ignore[code]` only with a reason. See `docs/development/type-safety.md`.
- CI (`.github/workflows/ci.yml`) runs ruff, black, Django checks, migration drift, mypy and pytest on SQLite (3.12/3.13) plus a PostgreSQL job. Local hooks are in `.pre-commit-config.yaml`.
- Comments/some verbose names are mixed Chinese/English; timezone is `Asia/Shanghai` with `USE_TZ=True`.

## Current gaps / gotchas

- **Migration reset already happened.** The old `core` migrations and the user group-seeding migrations were deleted and regenerated. A local pre-refactor `db.sqlite3` is incompatible: delete it and run `migrate` again. Do not use `--fake`.
- `db.sqlite3` is gitignored; `DJANGO_DB_PATH` points tests/CI at a temporary SQLite file.
- SQLite `select_for_update()` is a no-op. Unique constraints are the correctness backstop; the PostgreSQL CI job exercises real row locking.
- Content is stored as canonical text, not `JSONField`. Do not rely on ORM JSON key lookups; use projections (`TitleBinding`, `CategoryBinding`).
- `Block` currently targets users only; IP/range blocks and autoblock triggers are follow-ups.
- Protection has no cascading-transclusion or dedicated log-search UI yet.
- The MediaWiki `action=query/edit/move` adapter, web UI, parser, search, file upload/storage, category pages/member listings are not implemented.
- A prioritized historical defect list and status update lives in `docs/todo.md`; development guides live in `docs/development/`.
