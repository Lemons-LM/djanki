# Djanki

Djanki is a MediaWiki rewrite in Django. It keeps MediaWiki semantics at the edges
while using a cleaner internal model: one immutable revision per edit, named content
slots, titles and categories as rebuildable projections, structured protection and
blocks, and a versioned REST API.

## Status

The backend core is implemented and tested:

- unified `Revision` + `Content` + `RevisionSlot` model, global revid and readable slug
- page create/edit/move/delete/restore/protect/suppress services
- title properties with primary/aliases and release history
- category bindings projected from the properties slot
- structured page protection with change log
- block/unblock history with expiry
- DRF API at `/api/v1/`, OpenAPI at `/api/schema/`
- SQLite tests plus a PostgreSQL CI job; mypy, ruff and black in CI

The web UI, parser, search, file upload/storage and the MediaWiki `action=` adapter are
still planned.

## Quick start

```bash
uv sync --extra dev
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Then open `/api/docs/` or `/admin/`.

If your package mirror uses a private certificate, use `uv sync --extra dev --system-certs`.

## Documentation

- [All documentation](docs/index.md)
- [Project architecture](docs/arch/project.md)
- [Architecture decisions](docs/arch/decisions/index.md)
- [App documentation](docs/apps/index.md)
- [Development guide](docs/development/index.md)
- [Known tasks and history](docs/todo.md)

Documentation is mandatory in this repository: every code change must update the
matching file under `docs/` and add docstrings to public functions.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
