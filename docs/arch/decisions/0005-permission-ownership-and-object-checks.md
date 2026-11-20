# 0005 — Permission ownership and object-level checks

- Status: Accepted
- Date: 2026-11-20

## Context

All custom permissions were declared on `WikiUser`, so every codename had the `user`
app label even when it governed pages or files. The group-seeding migration also ran
during `migrate`, before Django's `post_migrate` created `Permission` rows, leaving
fresh databases with empty groups.

## Decision

Permissions belong to the model whose objects they govern:

| Model | Permissions |
| --- | --- |
| `core.SiteConfig` | `read`, `edit_interface`, `edit_content_model`, `import_data`, `export_data` |
| `core.Page` | `edit_page`, `move_page`, `delete_page`, `protect_page`, `suppress_page` |
| `file.File` | `upload_file`, `move_file`, `delete_file` |
| `user.WikiUser` | `block_user`, `unblock_user`, `change_user_rights`, `send_email`, `bot` |

Checks use Django permission strings (`core.edit_page`, `user.block_user`, ...).
A `MW_RIGHTS` mapping translates MediaWiki right names for the compatibility layer.

Group seeding moves to a `post_migrate` receiver plus an idempotent
`seed_groups` management command. The receiver explicitly ensures permissions exist,
sets each group's permission list exactly, and raises if a codename is missing.

## Object-level checks

`apps/core/permissions.py` exposes `can(user, action, page=None)` and `require(...)`.
It combines:

- global Django permission;
- account state (anonymous, inactive, deleted, currently blocked);
- page protection level (`open`, `autoconfirmed`, `sysop`);
- page deletion/suppression visibility;
- `SiteConfig.anonymous_read` for anonymous reads.

Django's `AnonymousUser.has_perm()` always returns `False`, so anonymous read is handled
explicitly rather than through the auth backend.

## Consequences

- Permissions appear under the correct content type and in the correct admin section.
- Fresh-database group seeding is deterministic.
- Services call `require()`; DRF permission classes call `can()` for early rejection.
- Page protection remains object-level; Django permissions alone are not sufficient.

## Rejected alternatives

- Keep all permissions on `WikiUser`: semantically wrong and awkward for API checks.
- A custom flat-rights backend: closer to MediaWiki names but much more custom auth code.
- Seed groups inside migrations: proved to fail before permissions exist.

## Follow-up

- Introduce a full `Block` model with history and expiry (P1-4).
- Add structured page-protection models and logs (P2-2/P2-8).
