# Repository Guidelines

## Project Structure & Module Organization
- `app/` is the Flask package; `__init__.py` exposes `create_app` and wires extensions.
- `app/models.py` holds SQLAlchemy models; keep new models colocated so migrations stay discoverable.
- `app/routes.py` defines the blueprint registered in the factory; add new blueprints under `app/` and register them in `create_app`.
- Root assets: `schema.sql` for the bootstrap schema, `requirements.txt` for runtime deps, and `DESIGN.md` for broader architectural context.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates/activates an isolated environment.
- `pip install -r requirements.txt` installs Flask, SQLAlchemy, Alembic, and related extensions.
- `flask --app app:create_app run --debug` starts the dev server on localhost with auto-reload.
- `flask --app app:create_app init-db` loads `schema.sql` into the configured MySQL instance via the custom CLI.
- `flask --app app:create_app seed-demo` populates synthetic datasets (~100 rows per table) for local development and demos.

## Coding Style & Naming Conventions
- Use PEP 8 conventions with 4-space indents; match the existing typing style (use annotations and module-level docstrings).
- Keep module names lowercase with underscores (`extensions.py`), and prefer noun-based class names for models.
- Group configuration constants inside `Config` and reference via `current_app.config` instead of importing globals.
- Format code with `black` (88-character line length) and organize imports per `isort` defaults; install them locally as dev-only tools.

## Testing Guidelines
- Add automated tests under a top-level `tests/` package mirroring the `app/` layout for clarity.
- Use `pytest` (add to dev dependencies) and name files `test_<module>.py`; fixtures can live in `tests/conftest.py`.
- Run `pytest` before opening a PR; aim to cover new routes, models, and CLI helpers, especially database interactions.

## Commit & Pull Request Guidelines
- Write imperative, present-tense commit subjects under 72 characters (e.g., `Add enrollment route error handling`).
- Squash work-in-progress commits locally; leave one commit per logical change when possible.
- PRs should describe the change, list manual or automated test results, and link any tracking issues.
- Include screenshots or curl examples when modifying HTTP responses so reviewers can verify behavior quickly.

## Security & Configuration Tips
- Provide secrets via environment variables or a local `.env`; `python-dotenv` will load them when present.
- Never commit real credentials—use placeholders in examples and rely on `SECRET_KEY`, `DATABASE_URI`, and `SCHEMA_PATH`.
- For local MySQL, create a dedicated user with limited privileges; document connection strings in issue notes, not in code.

## 补充要求

- 每次发送信息时，先阅读并做出全局规划，给出全局的修改意见。然后集中精力按条处理。对于每一条都要先写好规划，再进行代理。
- 每次修改都要写ConversationChanges.md文档，要求：每条记录要简洁，简单说明改动目的和被改动的文档与方法。
- 尽量用中文回复。
