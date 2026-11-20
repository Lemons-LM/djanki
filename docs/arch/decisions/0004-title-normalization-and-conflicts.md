# 0004 — Title normalization, URLs and conflicts

- Status: Accepted
- Date: 2026-11-20

## Context

Title uniqueness must behave consistently on SQLite and PostgreSQL, and MediaWiki-style
titles treat underscores, spaces, Unicode composition and first-letter case as equivalent.
Relying on database collation would produce different behaviour across backends.

## Decision

Normalize titles in Python and store both the display form and a normalized key:

1. Reject non-strings, empty titles, control characters and `# < > [ ] | { }`.
2. Split a known namespace prefix; unknown prefixes stay in the main namespace.
3. Unicode NFC; `_` → space; collapse whitespace; trim.
4. Apply first-letter capitalization for namespaces whose case rule requires it.
5. `normalized_title = NFC(display).casefold()`.
6. Enforce at most 255 characters and 255 UTF-8 bytes after casefolding.

Uniqueness and lookup use `(namespace, normalized_title)`, never database collation.

## URL semantics

- Canonical page: `/wiki/{namespace_prefix}{display_title}` (underscores in URLs).
- Alias: resolve, then 301 to the canonical primary URL.
- Redirect page: resolve, then 301 to the target's canonical URL (maximum 5 hops).
- Revision: `/r/{revid}` and `/r/p{page_id}-r{page_rev_number}`.

## Conflict semantics

| Situation | Result |
| --- | --- |
| Desired title active on another page during a normal edit | `409 title_conflict`, no mutation |
| Duplicate normalized titles in one page's set | `400 invalid_title` |
| Alias equals primary after normalization | `400 invalid_title` |
| Display-case-only change | release old binding, create new binding |
| Alias removed | release binding; history retained |
| Page deleted | release all active bindings |
| Restore with a title now owned elsewhere | `409 title_conflict`, rollback |
| Move to an occupied primary | `fail` → 409; `swap` → exchange primaries |

Ordinary edits never take over another page's title. Renames and takeovers go through
`move_page`, which requires the `move` permission.

## Consequences

- Behaviour is identical on SQLite and PostgreSQL.
- Changing a title's display case creates a new binding row, preserving history.
- Casefold expansion (for example `ß` → `ss`) is validated after folding.

## Rejected alternatives

- Database `lower()` uniqueness: backend-dependent and Unicode-incomplete.
- Case-sensitive titles: breaks MediaWiki expectations and produces duplicate-looking
  pages.

## Follow-up

- Extract the forbidden-character set into a configurable per-namespace policy.
