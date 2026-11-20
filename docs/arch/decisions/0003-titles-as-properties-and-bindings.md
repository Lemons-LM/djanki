# 0003 — Titles as properties and title bindings

- Status: Accepted
- Date: 2026-11-20

## Context

Titles previously existed in three places: `Page.current_title`, the JSON array
`PropRevision.titles`, and the unique `PageTitleIndex`. They could drift, and
`PageTitleIndex.page` was a `OneToOneField` while the rest of the code assumed a page
could hold multiple titles. Deleting a title also lost the page association.

## Decision

Titles are part of the `properties` slot:

```json
{
  "schema": 1,
  "titles": {
    "primary": "Main Page",
    "aliases": ["Home", "首页"]
  }
}
```

The primary title drives the canonical URL and page heading. Aliases are additional
active titles; resolving an alias returns a 301 to the canonical primary URL.

`TitleBinding` is a rebuildable projection:

- `page`, `namespace`, `display_title`, `normalized_title`, `is_primary`
- `created_revision`, `released_revision`, `created_at`, `released_at`

Rows are never physically deleted. Releasing a title sets `released_at` (the active
predicate) and, when available, `released_revision`. Re-adding a title creates a new row,
so the complete history remains queryable. A property edit is one revision; the title
service diffs the desired set against active bindings and releases/creates rows.

Partial unique constraints:

- active `(namespace, normalized_title)` — one page owns a title at a time.
- active primary per page — `(page)` where `is_primary` and `released_at IS NULL`.

## Consequences

- "Which page did this title previously belong to?" is a simple query on released rows.
- Title edits do not create one log row per title; they create one revision plus binding
  diffs.
- Deleting a page releases all of its titles without deleting history.
- Restoring a page can fail with `TitleConflict` if another page has since taken a title.

## Rejected alternatives

- One title per page with redirects only: simpler, but does not support true aliases.
- Keep `Page.current_title` as a second source of truth: guaranteed drift.
- Delete binding rows on release: loses the history the product requires.

## Follow-up

- Add a title-history special page backed by `TitleBinding` intervals.
- Add namespace-aware alias policy if cross-namespace aliases become required.
