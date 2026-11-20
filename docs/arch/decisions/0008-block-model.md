# 0008 — Block model with history and expiry

- Status: Accepted
- Date: 2026-11-20

## Context

`WikiUser` originally stored block state in inline fields: `is_blocked`, `block_page`,
`block_date_start` and `block_date_end`. That allowed only one block, had no reason or
issuer history, could not represent multiple blocks, and duplicated the meaning of
`is_active` / `is_deleted`.

## Decision

Add an append-only `user.Block` model:

- `target`, `blocked_by` (+ `blocked_by_name` snapshot), `reason`
- `start_at`, `expires_at` (`None` = indefinite)
- lift fields: `unblocked_at`, `unblocked_by`, `unblocked_by_name`, `unblock_reason`
- flags: `autoblock`, `no_create`, `is_deleted`

A block is active when it is not lifted/deleted, has started, and has not expired.
`WikiUser.is_currently_blocked` queries `Block.active_for(user)`. `block_user` and
`unblock_user` services are the only write path; unblocking lifts every active block.
The API exposes block/unblock/history endpoints and requires `user.block_user` /
`user.unblock_user`.

## Consequences

- Full block history, reasons, issuers and expiry are preserved.
- Multiple block rows can exist; active state is derived rather than a flag.
- Re-blocking creates a new row; unblocking lifts all active rows.
- Inline user fields are removed; callers must use the service or the reverse relation.

## Rejected alternatives

- Keep inline fields and add an audit table: still one active block and duplicated state.
- Store only `is_blocked` with a separate log: cannot answer "still active?" cheaply.

## Follow-up

- IP and range blocks (the current model targets `WikiUser`).
- Autoblock triggers and block appeals.
- Notifications/email on block and unblock.
