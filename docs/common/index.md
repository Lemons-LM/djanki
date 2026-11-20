# Common Tools

There are no shared utility packages yet. Cross-cutting helpers currently live with
their owning app:

- Title normalization: `apps/core/titles.py`
- Permissions: `apps/core/permissions.py`
- Read selectors: `apps/core/selectors.py`
- Content canonicalization: `apps/core/services/content.py`

`common/` and `infrastructure/` at the repository root are placeholders. Move a helper
here only when it is genuinely shared by multiple apps and has no domain dependency.
