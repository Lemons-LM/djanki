# Type Safety

The project uses mypy with django-stubs and djangorestframework-stubs. CI runs:

```bash
uv run mypy apps config
```

Configuration lives in `[tool.mypy]` and `[tool.django-stubs]` in `pyproject.toml`.

## Conventions

1. Add `from __future__ import annotations` to new modules that use modern unions or
   forward references.
2. Annotate every public service signature, including return types:
   ```python
   def block_user(*, target, blocked_by, reason: str = "", expires_at=None) -> Block:
   ```
3. Prefer concrete model types over `Any` where practical. For cross-app model imports
   that would create cycles, use `TYPE_CHECKING`:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from apps.user.models import WikiUser
   ```
4. Use Django string FK references (`"core.Page"`, `settings.AUTH_USER_MODEL`) rather
   than importing another app's model at module import time.
5. Do not silence errors broadly. A targeted ignore must include the error code and a
   reason:
   ```python
   value = external_library()  # type: ignore[no-untyped-call]  # untyped dependency
   ```
6. Keep `None` explicit. Model pointer fields such as `Page.current_revision`,
   `Revision.parent_revision` and `Revision.author` are nullable; narrow them with a
   local variable before use.

## Common fixes

### Optional model pointers

```python
revision = page.current_revision
if revision is None:
    raise RevisionStateError("The page has no current revision")
state = get_revision_state(revision)
```

### Paginator returns Optional

`PageNumberPagination.paginate_queryset()` is `list[T] | None`:

```python
blocks: list[Block] = paginator.paginate_queryset(queryset, request, view=self) or []
```

### Settings star imports

`config/settings/dev.py` and `test.py` use `from .base import *  # noqa: F403`.
Re-exported settings need explicit types in `base.py`, for example
`ALLOWED_HOSTS: list[str] = []`. Production settings must read required values with
`os.environ["NAME"]` so the type is `str` and startup fails fast.

### `.data` is not a plain list/dict

DRF serializer `.data` is a `ReturnList`/`ReturnDict`. If a function promises a plain
list, convert it: `return list(serializer.data)`.

## Third-party types

- Django comes from `django-stubs`; the plugin must stay configured in
  `[tool.mypy].plugins`.
- DRF comes from `djangorestframework-stubs`.
- For an untyped dependency, first look for a stubs package; otherwise use a narrow
  ignore with a comment, not a global `ignore_missing_imports` escape (the config
  currently sets it for missing packages, but typed packages should not be ignored
  silently).

## Adding types to old code

Work module by module: start with `apps/core/services`, `apps/core/permissions.py`,
`apps/user/services`, `apps/property/services`, then API serializers/views. Run mypy
after each module. Do not weaken the global configuration to make a single file pass;
fix the type or add a targeted ignore.
