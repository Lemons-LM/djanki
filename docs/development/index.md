# Development Documentation

This section is for contributors and future maintainers. Architecture decisions live
in [docs/arch/decisions](../arch/decisions/index.md); app behaviour lives in
[docs/apps](../apps/index.md).

| Document | Purpose |
| --- | --- |
| [setup.md](setup.md) | Local setup, settings, database reset, running the server |
| [testing.md](testing.md) | Test layout, fixtures, writing and running tests |
| [ci.md](ci.md) | GitHub Actions, pre-commit, PostgreSQL job, troubleshooting |
| [type-safety.md](type-safety.md) | mypy/django-stubs conventions and common fixes |
| [migrations.md](migrations.md) | Migration reset policy, review checklist, data migrations |

## Ground rules

1. Backend-first: services own write behaviour; views and serializers stay thin.
2. Every write is atomic and permission-checked in the service layer.
3. Revisions are immutable; projections (titles, categories) are rebuildable.
4. Documentation is mandatory: update the matching file in `docs/` and add docstrings
   to public functions (see `docs/index.md`).
5. CI must pass: `ruff`, `black --check`, `mypy`, Django checks, migration drift and
   `pytest`.
