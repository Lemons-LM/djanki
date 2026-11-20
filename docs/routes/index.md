# Routes

## Implemented (API)

See [API app](../apps/api/index.md) for request/response details.

| Method | Path |
| --- | --- |
| GET/POST | `/api/v1/pages/` |
| GET/DELETE | `/api/v1/pages/{id}/` |
| POST | `/api/v1/pages/{id}/edit` |
| GET | `/api/v1/pages/{id}/revisions/` |
| POST | `/api/v1/pages/{id}/restore` |
| POST | `/api/v1/pages/{id}/move` |
| POST | `/api/v1/pages/{id}/protect` |
| GET | `/api/v1/revisions/{revid-or-slug}/` |
| GET | `/api/v1/revisions/{revid-or-slug}/slots/` |
| GET | `/api/v1/titles/?title=...&namespace=0` |
| GET | `/api/v1/titles/bindings/?title=...` |
| POST | `/api/v1/users/{id}/block` |
| POST | `/api/v1/users/{id}/unblock` |
| GET | `/api/v1/users/{id}/blocks/` |
| GET | `/api/schema/`, `/api/docs/` |

`{revid-or-slug}` accepts a decimal global revid or `p{page_id}-r{page_rev_number}`.

## Planned (web UI)

The web UI is not implemented yet. The intended semantics are:

- Canonical page: `/wiki/{namespace_prefix}{display_title}`.
- Alias: resolve, then 301 to the canonical primary title.
- Redirect page: resolve, then 301 to the target's canonical title (max 5 hops).
- Revision permalink: `/r/{revid}` or `/r/p{page_id}-r{page_rev_number}`.
- Legacy-style permalink: `/wiki/{title}?oldid={revid}` for MediaWiki compatibility.

Title resolution and redirect-chain logic already exist in
`apps/core/services/titles.py::resolve_title`; the web layer only needs to turn the
result into redirects/responses.
