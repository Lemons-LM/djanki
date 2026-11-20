This is the Project's Architech on "What's new Comparing with MediaWiki" Documentation.

For all the Project's Architech Documentation, please go to the [Architect Doc Index](index.md).

For all the documentation, please go to the [All Doc Index](../index.md).

WARNING: If you write a code, you MUST write arch in the specific doc file in the [docs folder](..), and doc string on the function!!!

## New Architech

1. It's Python, not PHP.
2. All things are properties, even titles, and of core categories. So easy to update.
3. We want all MediaWiki tools, even functions, could be used on Djanki.
4. RESTful API. Not `api.php?action=xxx`.

## Implemented design choices

- **One revision is a complete snapshot.** MediaWiki has separate text/category
  concepts; Djanki stores one `Revision` with named slots (`main`, `properties`).
  A title edit and a text edit both produce a complete, permalinkable revision.
- **Global revid plus readable slug.** `Revision.id` is the MediaWiki-compatible
  numeric `oldid`; `p{page_id}-r{n}` is a short external slug.
- **Titles are properties with a binding projection.** `properties.titles` is the
  source of truth. `TitleBinding` is a rebuildable index that retains released rows,
  so title history and former page ownership remain queryable. Ordinary edits never
  steal an active title; moves are explicit.
- **Content-addressed storage.** Immutable `Content` rows are deduplicated by
  `(content_model, sha1)`, so unchanged slots are shared between revisions.
- **Permissions have a real owner.** Page rights live on `Page`, file rights on
  `File`, user rights on `WikiUser`, and site rights on `SiteConfig`. Object-level
  checks combine rights, blocks and page protection.
- **Compatibility at the edge.** The internal model is not shaped by
  `api.php?action=...`; a thin MediaWiki adapter can translate to the same services.
- **Operational state is explicit.** Page protection is a structured row per action
  with expiry and an append-only log; blocks are append-only history rows with derived
  active state. Neither is hidden in JSON or boolean flags.
- **Categories follow titles.** `CategoryBinding` is a release-preserving projection
  of `properties.categories`, maintained in the same revision transaction.
