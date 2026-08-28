# MC-IaaS Control Plane backend

Requires Python 3.12+ and Docker Compose.

```bash
cp .env.example .env
docker compose up -d
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Liveness is available at `GET /health`. Readiness, including the PostgreSQL check, is
available at `GET /ready`.

Run quality checks with:

```bash
python -m compileall app
ruff check .
pytest
```

Schema changes will be managed by Alembic. No domain migrations exist yet.
