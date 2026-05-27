# HR_Automation_SHAI

> End-to-end HR recruitment and onboarding automation for **SHAI Health** — a medical coding company.

Replaces the current mix of email-driven requisitions, paper application forms, ad-hoc spreadsheets, a standalone assessment tool, and Zoho Recruit with **one custom web platform** owned by the SHAI HR team — handing off cleanly to GreytHR for the post-hire employee lifecycle.

[![CI](https://github.com/Nithuh816/HR_Automation_SHAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Nithuh816/HR_Automation_SHAI/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Node](https://img.shields.io/badge/node-20%2B-brightgreen)
![License](https://img.shields.io/badge/license-Proprietary-lightgrey)

---

## What it does

The platform owns every step of the recruitment funnel:

1. **Requisition intake** — departments submit hiring requests; HR Head triages and assigns to a TA recruiter.
2. **Sourcing** — recruiters log leads from LinkedIn, Naukri, employee referrals, institutions, and cold calls; track progress against the 10-leads target.
3. **L1 — Application form** — digital form (replaces the paper Word template) filled at reception or via a magic link.
4. **L2 — Assessment** — in-house MCQ engine with auto-scoring and a configurable pass threshold.
5. **L3 — HR round** — recruiter scorecard (communication, total/relevant exp, salary, notice, LWD, location, stability, basic knowledge).
6. **L4 — Tech round (Team Lead)** — department-specific rubric.
7. **L5 — Tech round (Dept Head)** — final technical sign-off.
8. **L6 — Salary discussion** — TA TL runs the offer calculator + approval workflow.
9. **Documents** — secure upload portal with checklist branching for fresher vs. experienced.
10. **Offer letter + acceptance** — generated as PDF; candidate accepts via magic-link page.
11. **Onboarding handoff** — push to **GreytHR** via API; PR team picks up from there.

Cross-cutting: WhatsApp + email notifications, day-before joining reminders, SLA alerts, role-aware dashboards in the dark-violet style of `Dashboard_UI.png`, full audit log, DPDPA-aware PII handling.

## Architecture

```
                          ┌──────────────────────────────┐
                          │  React SPA (Vite + TS)       │
                          │  - Internal pages (MS SSO)   │
                          │  - Candidate pages (magic    │
                          │    link tokens, no account)  │
                          └──────────────┬───────────────┘
                                         │ HTTPS / JSON
                                         ▼
                          ┌──────────────────────────────┐
                          │  FastAPI (Python 3.12)       │
                          │  Routers · Services ·        │
                          │  Auth · Integrations · Jobs  │
                          └──┬───────────┬────────┬──────┘
                             │           │        │
                ┌────────────┘           │        └──────────────┐
                ▼                        ▼                        ▼
         ┌────────────┐         ┌────────────────┐       ┌──────────────┐
         │ PostgreSQL │         │ Redis + Celery │       │ S3-compatible│
         │            │         │ (jobs + beat)  │       │ object store │
         └────────────┘         └────────────────┘       └──────────────┘

External: Microsoft Graph (Teams + SSO) · GreytHR API · WhatsApp Cloud API · SMTP/Resend
```

Everything is containerised; the same `docker compose up` runs on a dev laptop, a SHAI VM, or any cloud VM/PaaS.

## Tech stack

| Layer       | Choice                                                                |
| ----------- | --------------------------------------------------------------------- |
| Backend     | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · Celery               |
| Frontend    | React 19 · TypeScript · Vite · Tailwind CSS · shadcn/ui · Recharts    |
| Data        | PostgreSQL 16 · Redis 7 · S3-compatible (MinIO / R2 / S3)             |
| Auth        | Microsoft 365 SSO (internal) · magic-link tokens (candidates)         |
| Comms       | WhatsApp Cloud API · SMTP / Resend                                    |
| Integrations| Microsoft Graph (Teams meeting create) · GreytHR API · pytesseract OCR|
| Tooling     | Docker Compose · GitHub Actions CI · ruff · mypy · eslint · vitest    |

## Repository layout

```
apps/
  api/                    FastAPI service
    app/
      auth/               MS SSO + magic-link
      core/               PII encryption, audit, PDF
      integrations/       Graph · GreytHR · WhatsApp · email · storage · OCR
      jobs/               Celery tasks (reminders, SLA, outbox)
      models/             SQLAlchemy ORM (per aggregate)
      routers/            FastAPI routers (per domain)
      schemas/            Pydantic request/response models
      services/           Business logic
      templates/          Jinja (emails + offer PDF)
    alembic/              Migrations
    tests/                pytest
  web/                    React SPA
    src/
      components/         Shared shadcn-based UI
      features/           Per-domain (requisitions, candidates, …)
      pages/              Top-level page shells
      candidate/          Candidate magic-link pages
      styles/             Tailwind tokens + dark-violet theme
docker-compose.yml        Local dev (api, web, postgres, redis, mailhog, minio, worker, beat)
.env.example              Documents every required env var
plan.md                   Full v1 roadmap, data model, page inventory, milestones
```

## Getting started

### Prerequisites

- **Python** 3.12+
- **Node.js** 20+ (LTS recommended)
- **Docker Desktop** with Compose v2

### First-time setup

```powershell
# 1. Copy and edit env vars (Azure AD app, GreytHR creds, etc.)
Copy-Item .env.example .env

# 2. Start infra (postgres, redis, mailhog, minio)
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

| URL                              | What                              |
| -------------------------------- | --------------------------------- |
| http://localhost:5173            | App                               |
| http://localhost:8000/docs       | API (Swagger)                     |
| http://localhost:8000/health     | API health probe                  |
| http://localhost:8025            | MailHog (captured dev emails)     |
| http://localhost:9001            | MinIO console (user/pass in .env) |

### Run everything in Docker

```powershell
docker compose up --build
```

## Testing

```powershell
# Backend
cd apps\api
pytest

# Frontend
cd apps\web
npm test          # vitest watch
npm test -- --run # vitest one-shot
npm run typecheck
npm run lint
```

CI runs the full matrix on every push and PR.

## Roadmap

The platform ships as **v1 big-bang** covering all 11 stages, built across milestones **M0 → M11**. See [`plan.md`](./plan.md) for the full architecture, data model, page inventory, integration design, security/PII posture, and per-milestone scope.

| Milestone | Status        | Scope                                                                       |
| --------- | ------------- | --------------------------------------------------------------------------- |
| M0        | ✅ Complete   | Monorepo, FastAPI + React skeletons, Docker, CI, dark-violet theme         |
| M1        | 🔜 Next       | DB models (users/depts/requisitions), MS SSO, RBAC, admin pages, seed       |
| M2        | ⏳ Planned    | Requisitions CRUD, triage inbox, assignment, HR Head dashboard              |
| M3        | ⏳ Planned    | Candidates, resume parsing, pipeline kanban, L1 application form            |
| M4        | ⏳ Planned    | Assessment engine (question bank + candidate-facing timed test)             |
| M5        | ⏳ Planned    | Interview scheduling, Teams integration, scorecards L3/L4/L5/L6             |
| M6        | ⏳ Planned    | Offer calculator, approval workflow, offer-letter PDF                       |
| M7        | ⏳ Planned    | Document upload portal, OCR validation, secure storage                      |
| M8        | ⏳ Planned    | Onboarding queue, **GreytHR API** handoff                                   |
| M9        | ⏳ Planned    | Notifications hub (email + WhatsApp), scheduled jobs                        |
| M10       | ⏳ Planned    | Dashboards + reports                                                        |
| M11       | ⏳ Planned    | DPDPA consent + retention, production overlay (Caddy + TLS), ops runbook    |

## Security

- **Internal access:** Microsoft 365 SSO + role-based access control.
- **Candidate access:** single-use magic-link tokens scoped per page (apply, assessment, schedule, upload, offer, confirm).
- **PII at rest:** Aadhaar / PAN / bank account fields encrypted with Fernet; encryption key in env.
- **Documents:** stored in an S3-compatible bucket; only short-lived presigned URLs are ever returned to clients.
- **Audit log:** every state transition, scorecard submit, offer change, document access, and GreytHR push is recorded.
- **Retention:** rejected-candidate PII purged after a configurable window (default 365 days); hired candidates retained.

Report security issues privately to the repo owner.

## Contributing

This is currently a single-tenant internal SHAI project. Each milestone ships as its own PR to `main`. Run `ruff format`, `mypy`, `eslint`, and the test suites locally before pushing.

## License

Proprietary — © SHAI Health.
