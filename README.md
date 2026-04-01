# Gogogo Backend

FastAPI service for **Gogogo**: user accounts, Telegram-linked profiles, ride offers and ride requests, background jobs, and integrations (e.g. image uploads, bot webhooks).

## Stack

- **Python** 3.13+
- **FastAPI** — HTTP API under `/api/v1`
- **PostgreSQL** (async via SQLAlchemy + asyncpg)
- **Alembic** — database migrations
- **Celery** + **Redis** — async tasks (queue `gogogo_queue`)
- **Cloudinary** — media (configured via env)

## Requirements

- [uv](https://github.com/astral-sh/uv) (recommended) or another way to install from `pyproject.toml` / `uv.lock`
- PostgreSQL
- Redis (for Celery)

## Configuration

Environment is selected with **`ENV_TYPE`**:

| `ENV_TYPE` | Env file loaded |
|------------|-----------------|
| `dev` (default) | `.env.local` |
| `prod` | `.env.prod` |
| `test` | `.env.test` |

**Base / database (required for app + migrations):**

- `ENV_TYPE`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`

**Optional / integrations:**

- `REDIS_URL` — Celery broker/backend (default `redis://localhost:6379/0`)
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `BOT_WEBHOOK_URL` — used by tasks that notify the Telegram bot
- `DB_POOL_CLASS` — e.g. `NullPool` for Celery workers (see deploy workflow)

## Local development

Install dependencies and run the API (dev reload):

```bash
cd gogogo-backend
uv sync --group dev
fastapi dev main.py --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs` (when using the dev server)

Apply migrations:

```bash
alembic upgrade head
```

Run Celery worker (from project root, with Redis available):

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info -Q gogogo_queue
```

### Docker (local API)

```bash
docker build -f docker/Dockerfile.local -t gogogo-backend-local .
docker run --rm -p 8000:8000 --env-file .env.local gogogo-backend-local
```

Production-style image uses `docker/Dockerfile.prod` and runs `fastapi run` with configurable `WORKERS` (default 4).

## API overview

All routes are prefixed with **`/api/v1`**:

- **`/users`** — register users (phone, name, etc.)
- **`/telegram`** — link and manage Telegram users (IDs, roles, patches)
- **`/rides`** — ride offers, ride requests, search, uploads, driver/passenger flows

Exact schemas and parameters are in the OpenAPI UI or the `app/representations` package.

## Tests

```bash
pytest
```

## Deployment

CI (`.github/workflows/deploy.yml`) builds `docker/Dockerfile.prod`, runs Alembic migrations in a one-off container, then starts the API container and a separate Celery worker container. Adjust paths such as `--env-file` and Docker network names to match your host.
