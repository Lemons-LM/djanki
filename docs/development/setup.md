# Local Setup

## Requirements

- Python >= 3.12 (Django 6 requires it)
- [uv](https://docs.astral.sh/uv/) for dependency management
- PostgreSQL only for production or the PostgreSQL CI job; SQLite is the default

## Install

```bash
git clone <repository>
cd djanki
uv sync --extra dev
```

If your environment uses a private package mirror with an unknown certificate:

```bash
uv sync --extra dev --system-certs
```

## Settings modules

| Module | Use |
| --- | --- |
| `config.settings.dev` | Default for `manage.py`; SQLite, `DEBUG=True` |
| `config.settings.test` | PostgreSQL CI settings; no SSL redirect |
| `config.settings.prod` | PostgreSQL, fail-fast env vars, secure cookies/HTTPS |

`manage.py` defaults to `config.settings.dev`. pytest is configured to use it as
well.

## Environment variables

Development:

- `DJANGO_DB_PATH` — optional SQLite path; useful for disposable test databases.

Production (`config.settings.prod`):

- `DJANGO_SECRET_KEY` — required; startup fails if missing
- `DB_NAME`, `DB_USER`, `DB_PASSWORD` — required
- `DB_HOST` (default `127.0.0.1`), `DB_PORT` (default `5432`)

PostgreSQL CI (`config.settings.test`): the same `DB_*` variables; defaults are
`djanki/djanki/djanki` on `127.0.0.1:5432`.

## Database

The project deliberately reset its core migrations and has no production data yet.
A database created before the reset is incompatible.

```bash
# Fresh development database
rm -f db.sqlite3
uv run python manage.py migrate
uv run python manage.py seed_groups   # idempotent, usually unnecessary after migrate
```

Use a temporary path for experiments:

```bash
rm -f /tmp/djanki-dev.sqlite3
DJANGO_DB_PATH=/tmp/djanki-dev.sqlite3 uv run python manage.py migrate
```

Do not use `migrate --fake` to bridge the old schema.

## Run

```bash
uv run python manage.py runserver
```

Useful URLs:

- `/admin/` — Django admin (create a superuser first)
- `/api/v1/` — REST API
- `/api/schema/` — OpenAPI document
- `/api/docs/` — Swagger UI

Create a superuser:

```bash
uv run python manage.py createsuperuser
```

## Everyday commands

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest -q
uv run ruff check .
uv run black --check .
uv run mypy apps config
```

## Troubleshooting

- **`UnknownIssuer` during `uv sync`** — the mirror certificate is not trusted by
  uv's bundled roots. Use `--system-certs` locally; CI uses public certificates.
- **`ValueError: Dependency on app with no migrations`** — run `makemigrations` for the
  app, or check that `apps.<name>.models` is imported from `models/__init__.py`.
- **Groups have zero permissions** — group seeding runs in `post_migrate`. Run
  `uv run python manage.py seed_groups` and re-check.
