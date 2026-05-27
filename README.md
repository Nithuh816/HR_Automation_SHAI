# HR_Automation_SHAI

Custom HR automation platform for SHAI Health — owns the recruitment-to-onboarding flow end to end and hands off to GreytHR for the employee lifecycle.

See the v1 plan at `~/.claude/plans/binary-coalescing-cupcake.md` (locally on the build machine) for full architecture, milestones, and scope.

## Stack

- **Backend:** Python 3.12 / FastAPI / SQLAlchemy / Alembic / Celery / Redis / PostgreSQL
- **Frontend:** React 19 / TypeScript / Vite / Tailwind CSS / shadcn/ui
- **Auth:** Microsoft 365 SSO (internal) + magic-link tokens (candidates)
- **Integrations:** Microsoft Graph (Teams), GreytHR API, WhatsApp Cloud API, S3-compatible storage
- **Dev / deploy:** Docker Compose, portable across cloud and self-host

## Repository layout

```
apps/
  api/   FastAPI service
  web/   React SPA
docker-compose.yml         Local dev: api, web, postgres, redis, mailhog, minio
docker-compose.prod.yml    Production overlay (Caddy + TLS) — added in M11
.env.example               Documents every required env var
```

## Prerequisites

- **Python** 3.12+
- **Node.js** 20+ (LTS recommended)
- **Docker Desktop** with Compose v2

## First-time setup

```powershell
# 1. Copy and edit env vars
Copy-Item .env.example .env

# 2. Start infrastructure (postgres, redis, mailhog, minio)
docker compose up -d postgres redis mailhog minio

# 3. Backend
cd apps\api
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 4. Frontend (in a second terminal)
cd apps\web
npm install
npm run dev
```

Then open:

- App: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- MailHog: http://localhost:8025
- MinIO console: http://localhost:9001 (user/pass in `.env.example`)

## Running everything in Docker

```powershell
docker compose up --build
```

## Tests

```powershell
# Backend
cd apps\api
pytest

# Frontend
cd apps\web
npm test
```

## OneDrive note

The repo currently lives inside OneDrive (`C:\Users\<user>\OneDrive\Desktop\HR_Automation_SHAI`). OneDrive sync can occasionally fight with `node_modules/`, `.venv/`, and `.git/` file locks. If you hit weird errors, move the repo outside OneDrive (e.g., `C:\dev\HR_Automation_SHAI`).
