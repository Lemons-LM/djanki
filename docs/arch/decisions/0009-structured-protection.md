# 0009 — Structured page protection and protection log

- Status: Accepted
- Date: 2026-11-20

## Context

`Page.protection` was an unvalidated JSON object. It had no expiry, no issuer, no
reason and no history. Permission checks read the JSON directly, so a typo or manual
database edit silently changed security behaviour.

## Decision

Add two core models:

- `PageProtection` — current row per `(page, action)` with `level`, `expires_at`,
  `set_by`, `set_by_name`, `set_at` and `reason`. The unique constraint is
  `(page, action)`; an expired row is inactive but remains until the next update.
- `ProtectionLog` — append-only `(old_level → new_level)` records with actor, reason,
  expiry and the current revision at the time of change.

`Page.protection_level(action)` returns the active level or `open`. The
`protect_page` service validates actions/levels, requires `core.protect_page`, checks
`base_revid`, updates rows and appends logs in one transaction. `protection={}` is not
a clear-all operation; pass `{"edit": "open"}` (or another action) explicitly.

## Consequences

- Protection is queryable and enforceable without parsing free-form JSON.
- Every level change is auditable.
- Expiry is checked at read time; no background job is required for correctness.
- `Page.protection` is removed; serializers expose `protection` as a simple
  `action → level` map and `protections` as full rows.

## Rejected alternatives

- Keep JSON and add a log: still no validation or expiry semantics.
- One row per protection event with a computed active row: more complex queries.
- Store protection as a revision: protection is operational state, not page content.

## Follow-up

- Cascading protection (protect pages transcluded into a protected page).
- Protection expiry notifications.
- A dedicated log search/special page.
