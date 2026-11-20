# 0001 — Unified revision model with content slots

- Status: Accepted
- Date: 2026-11-20

## Context

The original model had two independent revision streams (`PageRevision` for text and
`PropRevision` for JSON properties), each with its own current pointer on `Page`. A page
therefore had no single revision that represented its complete state. Permalinks, diffs,
recent changes and MediaWiki-compatible `oldid` lookups all required combining two IDs.
The title-sync `post_save` signal also wrote domain state and could recurse.

## Decision

One edit produces one `Revision`. The complete page state is stored as named `RevisionSlot`
rows, each pointing at an immutable `Content` row:

- `main` — wikitext or plain text.
- `properties` — canonical JSON holding titles, redirects and other properties.

`Page.current_revision` is the single current pointer. A property edit creates a new
revision that reuses the unchanged `main` `Content`; a text edit reuses the unchanged
`properties` `Content`. Every revision still carries both slots, so it is a complete
snapshot.

`Content` is content-addressed by `(content_model, sha1)` and is never modified.

## Consequences

- A single `revid` reconstructs the full page state.
- History, diffs, recent changes and logs use one timeline.
- Slot roles can grow later without changing `Revision`.
- Each revision has two slot rows even when only one changed; `Content` deduplication
  keeps storage reasonable.
- The database cannot enforce "exactly one main and one properties slot" across rows;
  `create_revision()` and tests enforce it.

## Rejected alternatives

- Keep two revision streams and add a global header table: still no full snapshot.
- One wide `Revision` table with nullable text/JSON columns: simpler but mixes content
  models and makes future slot types awkward.
- Store properties as `JSONField` on `Revision`: not content-addressed and backend
  normalisation makes deterministic dedup harder.

## Follow-up

- Add a content garbage collector for unreferenced `Content` rows.
- Add slot-level diff support if the API needs it.
