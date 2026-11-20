# CI and Local Hooks

## GitHub Actions

`.github/workflows/ci.yml` has two jobs.

### `sqlite` — Python 3.12 and 3.13

1. `uv sync --extra dev`
2. `uv run ruff check .`
3. `uv run black --check .`
4. `uv run python manage.py check`
5. `uv run python manage.py makemigrations --check --dry-run`
6. `uv run mypy apps config`
7. `uv run pytest -q`

The matrix catches syntax and typing differences between supported Python versions.

### `postgres`

Runs a `postgres:16` service and sets:

```
DJANGO_SETTINGS_MODULE=config.settings.test
DJANGO_SECRET_KEY=ci-secret-key
DB_NAME=djanki
DB_USER=djanki
DB_PASSWORD=djanki
DB_HOST=127.0.0.1
DB_PORT=5432
```

It runs Django checks and the full pytest suite with
`--ds=config.settings.test`. This is the only job that exercises real
`select_for_update()` row locking; SQLite treats it as a no-op.

## Pre-commit

`.pre-commit-config.yaml` runs local hooks:

- `ruff check .` on commit
- `black --check .` on commit
- `pytest -q` on pre-push

Install once:

```bash
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
uv run pre-commit run --all-files
```

Hooks use `language: system`, so they run the versions installed by `uv`.

## Reproducing CI locally

```bash
uv sync --extra dev --system-certs   # --system-certs only for private mirrors
uv run ruff check .
uv run black --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run mypy apps config
uv run pytest -q
```

## Adding a CI step

Add a step to the `sqlite` job unless it requires PostgreSQL. Keep steps fast and
deterministic; do not install ad-hoc tools that are not in `pyproject.toml` or the
lockfile. If a tool becomes part of the workflow, add it to the `dev` extra and lock
it with `uv lock`.

## Troubleshooting

- **Certificate errors in `uv sync`** — use `--system-certs` locally. CI runners use
  public roots and do not need it.
- **PostgreSQL connection refused** — the service needs a few seconds to start; the
  health check in the workflow handles this. Locally, verify `pg_isready`.
- **Mypy version drift** — `django-stubs[compatible-mypy]` pins a compatible mypy.
  Upgrade the stubs and mypy together, then rerun `uv lock`.
