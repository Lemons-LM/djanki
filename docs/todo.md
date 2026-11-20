# Djanki TODO

Status as of 2026-11-20. The original P0/P1 defect list has been resolved or superseded
by the core refactor; this document tracks the remaining work. Development guides are
in [development](development/index.md).

## Completed

- Unified `Revision` + `Content` + `RevisionSlot`; one revision is a complete snapshot.
- Global numeric revid plus readable `p{page_id}-r{number}` slug.
- Page create/edit/move/delete/restore/protect/suppress services with transactions and
  `base_revid` conflict detection.
- Titles as properties with primary/aliases and release-preserving `TitleBinding`.
- Category bindings projected from `properties.categories` with release history and a
  rebuild command.
- Structured `PageProtection` + append-only `ProtectionLog`.
- Append-only `Block` history with expiry, block/unblock services and API.
- Per-model permissions, `post_migrate` group seeding, object-level `can()`/`require()`.
- DRF `/api/v1/`, OpenAPI, error envelope, anonymous-read policy.
- SQLite test matrix, PostgreSQL CI job, pre-commit, mypy/django-stubs, LICENSE.
- English architecture, app, API, route and development documentation.

## Remaining backlog

### P1 — correctness and architecture

| Item | Location | Acceptance |
| --- | --- | --- |
| IP/range blocks and autoblock triggers | `apps/user/models/block.py`, services | A block can target an IP/range without a `WikiUser`; active checks cover anonymous requests. |
| Uniform service result types | `apps/core/services/*` | Write services return an explicit result/command object instead of a mix of model, `None` and exceptions. |
| Parser boundary | `apps/parser`, `apps/core/services/` | One parser entry point exists; `core` depends only on its interface. |
| Content garbage collection | `apps/core` | A command deletes `Content` rows with no slots and reports reclaimed bytes. |

### P2 — MediaWiki compatibility and domain modelling

| Item | Location | Acceptance |
| --- | --- | --- |
| Namespace registry as data | `apps/core/namespaces.py` | Namespaces can be added without a code change; UI/API expose names and case rules. |
| MediaWiki action API adapter | `apps/api/mediawiki/` | `action=query/edit/move` translates to core services; no domain logic in the adapter. |
| Revision metadata/diff | `apps/core/models/revision.py`, API | Parent/size/sha1/minor/bot plus slot-level diff and revision comparison endpoints. |
| Content models/slots | `apps/core/constants.py`, services | Additional slot roles and content models can be created without changing `Revision`. |
| Category pages/member listings | `apps/property` | Query active `CategoryBinding` rows for members; handle category rename/move. |
| Cascading protection | `apps/core/protection.py` | Protect pages transcluded into a protected page; add tests for the cascade. |
| Unified operation log/special page | `apps/special`, core/user/property | Move/delete/protect/block/upload events queryable by target and time. |
| i18n | models/API/docs | `gettext_lazy`, message files and a documented language policy. |
| Title collation/limits | `apps/core/titles.py` | Documented and tested character/byte limits and namespace case rules. |

### P3 — engineering and operations

| Item | Location | Acceptance |
| --- | --- | --- |
| Coverage and factories | `pyproject.toml`, tests | `pytest-cov` threshold in CI; shared factories for pages/revisions/users. |
| Static/media/logging config | `config/settings/base.py`, `prod.py` | `MEDIA_URL`, `STATICFILES_DIRS`, structured logging and proxy SSL header. |
| Remaining app docs | `docs/apps/extension`, `parser`, `search`, `special`, `webui` | Each empty app doc has scope, interfaces and non-goals. |
| Web UI | `apps/webui` | Title resolution → 301 alias/redirect semantics and page rendering are implemented. |
| File upload/storage | `apps/file` | Storage backend, upload/download endpoints and file revisions/metadata. |
| Search | `apps/search` | Index rebuild from revisions and a query API. |
| Extension/hook system | `apps/extension` | Documented hook points and a safe extension registration API. |
| Template support | `apps/template` | Template parsing/transclusion integrated with the parser. |
| Production hardening | settings/API | OAuth/bot passwords, rate limiting, `CSRF_TRUSTED_ORIGINS`, secret rotation guidance. |
| Performance regression tests | API/tests | Query-count assertions for page lists, revision history and title/category lookups. |
| Production migration plan | docs/development/migrations.md | A migration path from the reset schema to a release deployment. |

## Historical note

The pre-refactor audit identified circular non-null page foreign keys, three title
sources of truth, a broken title-sync signal, split revision IDs, permission seeding
before `Permission` creation, non-atomic writes, and broken category timestamps. Those
issues were resolved by the model reset and the services described in the ADRs.
