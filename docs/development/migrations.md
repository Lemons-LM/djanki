# Migrations

## Current policy

The project is pre-release and has no production data. The core schema was reset once
to remove the old text/property revision split and the circular `Page` foreign keys.
Further incompatible changes may reset migrations again until a release is declared.

Rules:

- Generated migrations are committed.
- Never edit historical migrations that have been applied in a shared environment,
  except to add a data migration.
- Do not use `migrate --fake` to bridge an incompatible reset.
- Local developers with an old `db.sqlite3` must delete it and run `migrate` again.

## Commands

```bash
uv run python manage.py makemigrations
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run python manage.py migrate --plan
```

CI runs `makemigrations --check --dry-run`, so an ungenerated model change fails the
build.

## Data migrations

Use data migrations only for deterministic seed data that must run during migrate:

- `core/0002_seed_site_config.py` creates the `SiteConfig` singleton.

Do **not** seed groups or permissions in a migration. `Permission` rows are created in
`post_migrate`; a migration that queries them sees an empty table on a fresh database.
Groups are seeded by `apps/user/groups.py` through a `post_migrate` receiver and the
`seed_groups` command.

## Adding a model or field

1. Add/update the model and `apps/<app>/models/__init__.py` export.
2. Run `makemigrations <app>`.
3. Inspect the generated migration: dependencies (especially `settings.AUTH_USER_MODEL`),
   `on_delete`, constraints and indexes.
4. Run `migrate` on a fresh temporary database, not only on the dev database.
5. Run `pytest`; update `tests/test_fresh_migrate.py` if seeding or singleton data
   changed.
6. Update the app doc in `docs/apps/<app>/index.md` and, for a material decision, add
   an ADR.

## Migration review checklist

- [ ] No circular non-null foreign keys.
- [ ] `on_delete` is intentional (`PROTECT` for history, `SET_NULL` for optional
      attribution, `CASCADE` only for pure children such as slots).
- [ ] Constraints enforce the important invariants (unique active title/category,
      unique `(page, page_rev_number)`).
- [ ] Indexes cover the documented lookup paths.
- [ ] No group/permission seeding in migrations.
- [ ] Fresh-database migrate and tests pass.
- [ ] Docs and type checks are updated.
