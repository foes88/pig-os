# PigOS — Local Development

## Prerequisites
- Docker + Docker Compose
- Python 3.12 + [uv](https://docs.astral.sh/uv/)
- Node.js 22

## 1. Backend + DB + Redis (Docker)
```bash
docker compose up -d        # postgres + redis + api
```
The API is served at http://localhost:8000 (`GET /health` → `{ "status": "ok" }`).

### Run the API outside Docker
```bash
cd api
cp .env.example .env        # adjust DATABASE_URL / SECRET_KEY
uv sync
uv run alembic upgrade head # apply migrations
uv run uvicorn app.main:app --reload
```

### Seed master data
```bash
cd api && uv run python scripts/seed_master.py
```

## 2. Frontend
```bash
cd src
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                 # http://localhost:3000
```

## 3. Tests / checks
```bash
cd api && uv run pytest tests/ -q       # backend
cd src && npx tsc --noEmit              # frontend type check
cd src && npx vitest run                # frontend unit tests
```

## Notes
- Multi-tenant: every tenant-scoped table carries `farm_id`; access is farm-membership filtered.
- API version prefix is fixed at `/api/v1`.
- Do not commit real secrets — `.env*` are git-ignored; only `.env.example` is tracked.
