# User App

`apps/user` owns the custom user model, groups and permission seeding. See
[ADR 0005](../../arch/decisions/0005-permission-ownership-and-object-checks.md).

## WikiUser

`WikiUser(AbstractUser)` adds:

- `phone`, `real_name`
- `is_deleted`
- `is_currently_blocked` property

Block state is not stored on the user. It lives in the append-only `Block` model and
is derived through `Block.active_for(user)`.

## Blocks

`Block` stores:

- `target`, `blocked_by` / `blocked_by_name`, `reason`
- `start_at`, `expires_at` (`None` = indefinite)
- lift fields: `unblocked_at`, `unblocked_by` / name, `unblock_reason`
- `autoblock`, `no_create`, `is_deleted`, `created_at`

A block is active when it is not lifted/deleted, has started and has not expired.
`block_user()` creates a new history row; `unblock_user()` lifts every active block and
returns the count. Both require the corresponding `user.block_user` /
`user.unblock_user` permission. Blocking yourself, blocking a deleted user, or setting
a past expiry raises `InvalidBlock`.

API:

- `POST /api/v1/users/{id}/block`
- `POST /api/v1/users/{id}/unblock`
- `GET /api/v1/users/{id}/blocks/`

The old inline fields (`is_blocked`, `block_page`, `block_date_start`,
`block_date_end`) were removed.

## Permission ownership

| Model | Permissions |
| --- | --- |
| `core.SiteConfig` | `read`, `edit_interface`, `edit_content_model`, `import_data`, `export_data` |
| `core.Page` | `edit_page`, `move_page`, `protect_page`, `suppress_page` |
| `file.File` | `upload_file`, `move_file`, plus Django's built-in `delete_file` |
| `user.WikiUser` | `block_user`, `unblock_user`, `change_user_rights`, `send_email`, `bot` |

Django also creates the standard `add_*`, `change_*`, `delete_*`, `view_*`
permissions. Page deletion uses the built-in `core.delete_page`.

## Groups

`apps/user/groups.py` defines:

| Group | Permissions |
| --- | --- |
| `user` | read, edit, move |
| `autoconfirmed` | user + send_email, upload_file |
| `sysop` | read, edit, move, delete, protect, import, export, block, unblock |
| `interface-admin` | read, edit_interface, edit_content_model |
| `bot` | read, edit, bot |
| `suppress` | read, suppress_page |
| `bureaucrat` | read, change_user_rights |

Groups are seeded by a `post_migrate` receiver and can be rerun with:

```bash
uv run python manage.py seed_groups
```

Seeding is idempotent and replaces each group's permission set, so stale assignments
are removed.

## Object-level checks

`apps/core/permissions.py` provides `can(user, action, page=None)` and `require(...)`.
They combine:

- the global Django permission;
- account state (anonymous, inactive, deleted, currently blocked);
- page protection level (`open`, `autoconfirmed`, `sysop`);
- deleted/suppressed page visibility;
- `SiteConfig.anonymous_read` for anonymous reads.

Write services call `require()`. API permission classes call `can()` for early
rejection; the service check remains authoritative.

## Tests

```bash
uv run pytest apps/user/tests -q
```

Tests cover group seeding/idempotency, block/unblock, expiry, self-block rejection and
permission checks.
