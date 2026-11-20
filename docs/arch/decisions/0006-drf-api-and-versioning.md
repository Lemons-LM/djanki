# 0006 — DRF API, versioning and optimistic concurrency

- Status: Accepted
- Date: 2026-11-20

## Context

The project promises a RESTful API rather than MediaWiki's `api.php?action=...`, while
also wanting MediaWiki tools to remain usable. There was no API framework, route or
serializer in the repository.

## Decision

- Use Django REST Framework with `drf-spectacular`.
- Expose `/api/v1/` with explicit versioning; `/api/schema/` and `/api/docs/` for OpenAPI.
- Authentication: session for browser clients, token for tools; no JWT initially.
- All mutations require `base_revid`. A mismatch returns `409 edit_conflict` with the
  current revid and slug.
- Errors use one envelope:

```json
{
  "error": {
    "code": "edit_conflict",
    "message": "The page changed since base_revid.",
    "details": {"base_revid": 10, "current_revid": 11, "current_slug": "p7-r5"}
  }
}
```

- MediaWiki `action=query/edit/move` compatibility is a thin adapter at the edge. It
  translates to the same services; the domain model is not shaped by `action=`.

## Endpoints (first version)

- `GET/POST /api/v1/pages/`
- `GET /api/v1/pages/{id}/`
- `POST /api/v1/pages/{id}/edit`
- `GET /api/v1/pages/{id}/revisions/`
- `DELETE /api/v1/pages/{id}/`
- `POST /api/v1/pages/{id}/restore`
- `POST /api/v1/pages/{id}/move`
- `POST /api/v1/pages/{id}/protect`
- `GET /api/v1/revisions/{revid-or-slug}/`
- `GET /api/v1/revisions/{revid-or-slug}/slots/`
- `GET /api/v1/titles/?title=...`
- `GET /api/v1/titles/bindings/?title=...`

## Consequences

- API views stay thin; all writes go through domain services.
- `base_revid` prevents lost updates.
- Pagination is mandatory for revision and binding history.
- The MediaWiki adapter can be added without changing core models.

## Rejected alternatives

- Django Ninja: good type-first/async option, but DRF's permission and ecosystem maturity
  wins for the first implementation.
- Plain Django views: too much custom serialization/auth/pagination work.
- Implementing `action=` first: would leak MediaWiki's API shape into the domain.

## Follow-up

- Add OAuth/bot-password authentication.
- Build the `/w/api.php` adapter over the same services.
