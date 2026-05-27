# HR_Automation_SHAI — v1 Plan

> Big-bang v1 covering the full recruitment-to-onboarding flow for SHAI Health, replacing email-driven requisitions, paper forms, the standalone assessment tool, and Zoho Recruit with a single custom platform that hands off to GreytHR.

## Context

**SHAI Health** (medical coding company) currently runs its full HR recruitment-to-onboarding flow manually with email-driven requisitions, paper application forms, ad-hoc spreadsheets, a separate in-house assessment tool, **Zoho Recruit** for candidate applications + offer letters, and **GreytHR** for downstream onboarding. The user wants to **replace** all of this (except GreytHR, which stays as the final onboarding system) with a single custom web application owned end-to-end.

Decisions locked at project kick-off:

- **Custom orchestration platform** — no Zoho.
- **Tech stack:** Python **FastAPI** backend + **React** SPA frontend.
- **Scope:** Big-bang v1 — all 11 stages of the flow (Requisition → GreytHR handoff) shipped together.
- **Internal auth:** **Microsoft 365 SSO** (SHAI already uses Teams).
- **Hosting:** Portable design (Docker), deploy target decided after Phase 1 build is running locally.
- **Assessment software:** Rebuilt in-house inside this app (replaces the existing standalone tool).
- **GreytHR API access:** Confirmed available; used for onboarding handoff.
- **Target visual style:** the dark-violet HR-dashboard mock in `Dashboard_UI.png`.
- **Team scale today:** 4 TA members (incl. TL); ~10–30 total internal users across HR Head, TA, dept leads, dept heads, PR.

---

## High-level architecture

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
                          │  FastAPI app (Python 3.12)   │
                          │  Routers · Services ·        │
                          │  Auth · Integrations · Jobs  │
                          └──┬───────────┬────────┬──────┘
                             │           │        │
                ┌────────────┘           │        └──────────────┐
                ▼                        ▼                        ▼
         ┌────────────┐         ┌────────────────┐       ┌──────────────┐
         │ PostgreSQL │         │ Redis + Celery │       │ S3-compatible│
         │            │         │                │       │ object store │
         └────────────┘         └────────────────┘       └──────────────┘

External integrations:
  - Microsoft Graph    → Teams meeting create, SSO/userinfo, calendar
  - GreytHR API        → push new-hire to onboarding
  - WhatsApp Cloud API → candidate comms
  - Email provider     → SMTP / Resend
  - OCR                → pytesseract (local) for Aadhaar/PAN/marksheet validation
```

Everything is containerised; no platform-locked APIs. Same `docker compose up` works on a dev laptop, a SHAI VM, or any cloud VM/PaaS.

---

## Tech stack

**Backend (`apps/api/`)**

- Python 3.12, FastAPI 0.115+, Uvicorn
- SQLAlchemy 2.0 + Alembic migrations
- Pydantic v2 schemas
- PostgreSQL 16
- Celery + Redis for scheduled & async jobs (day-before reminders, SLA alerts, GreytHR retries, email/WhatsApp send)
- python-msal for Microsoft Entra ID OAuth
- httpx for all outbound HTTP (Graph, GreytHR, WhatsApp, email)
- boto3 against an S3-compatible interface (Cloudflare R2 / MinIO / AWS S3 — chosen by env vars)
- pdfplumber, python-docx, pytesseract for resume parsing / OCR
- WeasyPrint for offer-letter PDF generation
- structlog for structured logging
- pytest + httpx test client for tests

**Frontend (`apps/web/`)**

- React 19 + TypeScript + Vite
- Tailwind CSS + shadcn/ui components
- TanStack Query for server state, React Hook Form + Zod for forms
- React Router v7
- Recharts for dashboards
- MSAL.js for Microsoft SSO redirect flow
- axios wrapper for API calls

**DevOps**

- Docker Compose for local dev (api, web, postgres, redis, mailhog, minio)
- Multi-stage Dockerfile per app for production
- GitHub Actions CI: lint, typecheck, tests, build images
- `.env.example` documents every required var; pydantic-settings loads them

---

## Data model (core entities)

~25 tables. Highlights only — full ORM defined in `apps/api/app/models/`.

**Identity & org**
- `users` (id, ms_oid, email, name, role enum, team enum, department_id, manager_id, active)
- `departments` (id, name, head_user_id)

**Requisition**
- `requisitions` (id, code, dept, title, jd_md, headcount, exp range, budget range, urgency, status, assigned_recruiter_id, due_by, sla_breached_at)
- `requisition_comments`

**Candidate & application**
- `candidates` (personal + experience + sourcing fields; resume_storage_key)
- `candidate_applications` (candidate × requisition, stage enum, stage_entered_at, rejection metadata)
- `application_form_l1` (JSON payload mirroring the Word form)

**Assessment**
- `assessment_templates`, `questions`, `template_questions`
- `assessment_attempts`, `assessment_answers`

**Interviews**
- `interviews` (round, mode, scheduled_at, interviewer_id, teams_join_url, status)
- `scorecards` (rubric fields keyed per round, overall_rating, decision)

**Offer**
- `offers` (calculated CTC components, joining_date, status, approval chain)
- `offer_letter_pdfs`, `offer_letter_templates`

**Documents**
- `document_checklists` (fresher vs experienced)
- `documents` (per candidate; PII-encrypted; OCR-extracted JSON)

**Onboarding handoff**
- `onboarding_handoffs` (greythr_employee_id, push status, retries)

**Notifications, security, infra**
- `notifications` (in-app + email + WhatsApp outbox)
- `email_templates`, `whatsapp_templates`
- `magic_links` (candidate tokens, scoped per page, single-use)
- `integrations` (encrypted config for GreytHR, Graph, WhatsApp)
- `audit_log` (every transition)

PII at rest: Aadhaar / PAN / bank account numbers Fernet-encrypted at the column level. Document files in object store; presigned URLs ≤5 min TTL.

---

## Page inventory (all 11 stages)

**Internal (Microsoft SSO required)**

- `/login`, `/`
- Dashboards: `/dashboard` (role-aware: HR Head / TA TL / TA Recruiter / Dept Head / PR view)
- Requisitions: `/requisitions`, `/requisitions/inbox`, `/requisitions/new`, `/requisitions/:id`, `/requisitions/:id/assign`, `/requisitions/:id/edit`
- Candidates: `/candidates`, `/candidates/new`, `/candidates/import`, `/candidates/:id`, `/candidates/:id/applications/:appId`
- Pipeline: `/pipeline`, `/pipeline/:reqId` (kanban)
- Sourcing: `/sourcing/referrals`, `/sourcing/leads/:reqId`
- Interviews: `/interviews/today`, `/interviews/:id`, `/interviews/:id/scorecard`, `/calendar`
- Assessment: `/assessment/templates`, `/assessment/templates/new`, `/assessment/templates/:id/edit`, `/assessment/questions`, `/assessment/results/:appId`
- Documents: `/settings/checklists`, `/candidates/:id/documents`
- Offers: `/offers`, `/offers/:id`, `/settings/offer-templates`
- Onboarding: `/onboarding/queue`, `/onboarding/:id`
- Settings: `/settings/users`, `/settings/departments`, `/settings/integrations`, `/settings/templates`, `/settings/rubrics`, `/settings/audit-log`
- Reports: `/reports/funnel`, `/reports/time-to-fill`, `/reports/source-of-hire`, `/reports/recruiter-performance`, `/reports/drop-offs`

**Candidate-facing (magic-link, no account)**

- `/c/apply/:token` — L1 application form
- `/c/assessment/:token` — L2 timed MCQ
- `/c/schedule/:token` — pick interview slot
- `/c/upload/:token` — document upload portal
- `/c/offer/:token` — view & accept/decline offer
- `/c/confirm/:token` — day-before joining confirmation

Magic-link TTLs: forms 7d, scheduler 14d, assessment 48h after issue (≤90 min once started), offer 7d, confirmation 48h.

---

## Backend domains

REST under `/api/v1`. Internal routes require MS-SSO bearer; `/api/v1/c/*` accepts a magic-link token.

- `auth/` — SSO callback, `/me`, magic-link verify
- `requisitions/` — CRUD, assign, close, list candidates
- `candidates/` — CRUD, resume upload, application attach
- `applications/` — advance, reject, timeline
- `interviews/` — schedule (creates Teams meeting), reschedule, scorecard
- `assessments/` — admin CRUD; candidate start/answer/submit
- `documents/` — candidate upload (queues OCR), signed URL fetch
- `offers/` — auto-calc, approval, send, accept
- `onboarding/` — push to GreytHR, status, confirm joining
- `notifications/`, `reports/`, `settings/`

Stage transitions are guarded by a single state machine in `services/pipeline.py`: only the role allowed at the current stage may transition.

---

## Integrations

**Microsoft Graph (SSO + Teams)**
- App registration in SHAI's Entra ID; scopes: `User.Read`, `OnlineMeetings.ReadWrite`, `Calendars.ReadWrite.Shared`.
- SSO: PKCE auth-code via MSAL.js → backend exchanges code → our own short-lived JWT.
- Teams meeting created on every interview schedule.

**GreytHR**
- HTTPX client; auth method per their plan (API key / OAuth); creds entered in `/settings/integrations`.
- Single v1 op: create employee from accepted offer + collected docs. Idempotent via application_id ↔ employee_id mapping.
- Celery-retried on transient failure.

**WhatsApp Cloud API (Meta)**
- Free tier ~1k conversations/month.
- Templates pre-approved in Meta business manager; template IDs + variable maps stored locally.
- Outbox pattern: enqueue → worker sends → webhook updates status.

**Email**
- Provider-agnostic interface; default impls: Resend and SMTP (so SHAI can use their own M365 SMTP).

**OCR / resume parsing**
- pytesseract (Tesseract binary in Docker image) for ID images; regex for Aadhaar (12 digits), PAN (AAAAA9999A).
- pdfplumber / python-docx for resumes.
- Never auto-reject — low-confidence extractions go to a manual-review queue.

**Object storage**
- Thin facade (`put`, `presigned_get`, `delete`) with implementations for local-fs (dev), MinIO (dev/self-host), Cloudflare R2 (cloud). Selected by `STORAGE_BACKEND` env.

---

## Background jobs (Celery)

- `reminders.send_day_before_joining_confirmation` — hourly; picks offers with joining_date = tomorrow.
- `reminders.send_interview_reminder` — every 15 min; T-24h, T-2h, T-15m.
- `reminders.send_doc_chase` — daily; chases offers missing required docs.
- `sla.check_requisition_sla` — daily; flags reqs past due_by or with <10 sourced after configurable days.
- `outbox.deliver_email`, `outbox.deliver_whatsapp` — process queued notifications.
- `greythr.push_employee` — invoked on PR action; retried.
- `assessment.expire_attempts` — closes attempts past their time limit.

All tasks idempotent. Beat schedule in `jobs/celery_app.py`.

---

## Security & compliance

- **MS-SSO** for all internal access; **RBAC** enforced by FastAPI dependencies.
- **Magic-link tokens** for candidates: 32-byte random, single-use per scope, HMAC-bound to scope + application_id.
- **PII encryption** at the column level via Fernet (key rotated annually).
- **Document URLs** short-lived presigned (≤5 min); never returned in JSON lists.
- **Audit log** on every state transition, scorecard, offer change, document access, GreytHR push, role change.
- **Retention:** rejected candidate PII purged 365 days after last activity (configurable); hired candidates retained.
- **DPDPA consent** on candidate-facing pages; timestamped.
- All secrets via env vars; never committed.
- HTTPS enforced in production (Caddy/Traefik in `docker-compose.prod.yml`).

---

## Design system

Dark-violet theme matching `Dashboard_UI.png`:

- Background `#1a0d2e` (deep purple), surface `#2a1745`, accent `#a855f7` (violet 500), success `#10b981`, warning `#f59e0b`, danger `#ef4444`.
- Tailwind tokens at `apps/web/src/styles/index.css`; shadcn components themed via CSS variables.
- Cards: soft inner shadow + 12px radius; charts: violet-on-dark.
- Typography: Inter for UI, JetBrains Mono for codes/IDs.

---

## Milestones

| M | Scope | Effort |
|---|-------|--------|
| **M0** | Monorepo scaffold, Docker Compose, FastAPI + React skeletons, dark-violet theme, CI | 3–5d |
| **M1** | User/Dept/Requisition models, **MS SSO**, RBAC, admin pages, seed | 4–6d |
| **M2** | Requisitions CRUD, triage inbox, assignment, HR Head dashboard | 4–5d |
| **M3** | Candidates CRUD, resume parsing, pipeline kanban, magic-link infra, **L1 form** | 6–8d |
| **M4** | **Assessment engine** (templates, question bank, candidate-facing timed test) | 5–7d |
| **M5** | Interview scheduling, **Teams integration**, scorecards L3/L4/L5/L6, rubric editor | 7–10d |
| **M6** | Offer calculator, approval, **offer letter PDF**, candidate accept | 4–6d |
| **M7** | Document portal, OCR validation, encrypted storage | 5–7d |
| **M8** | Onboarding queue, **GreytHR API** integration, joining confirmation | 4–6d |
| **M9** | Notifications hub (email + WhatsApp), templates, scheduled jobs | 5–7d |
| **M10** | Dashboards & reports | 4–6d |
| **M11** | DPDPA consent + retention, production overlay, ops runbook | 4–5d |

**Estimate: ~55–80 focused days (~11–16 weeks).** Re-estimate after M0 once we have real velocity data.

Each milestone ships as its own PR to `main`. There is no production release until M11; intermediate milestones are reviewable locally via `docker compose up`.

---

## Verification (post-M11 walkthrough)

1. Sign in as HR Head (MS SSO).
2. Create a requisition; assign to a TA recruiter.
3. As recruiter, add 10 candidates (one via resume upload, others manual).
4. Send L1 link to one candidate; candidate fills it.
5. Trigger assessment; candidate completes it; score crosses threshold.
6. Schedule L3, L4, L5, L6; submit scorecards from respective roles.
7. Build offer; approve; send; candidate accepts on `/c/offer/:token`.
8. Candidate uploads all required docs.
9. Confirm joining; verify day-before email fires.
10. PR pushes to GreytHR; verify GreytHR employee created (sandbox tenant).
11. Confirm audit log captures all transitions.

---

## Open items requiring input

1. **Azure AD / Entra ID app registration** — Tenant ID, Client ID, Client Secret (scopes listed under §Integrations).
2. **GreytHR API docs / sandbox** — reference + a test account.
3. **WhatsApp Business account** — Meta Business Manager + a WhatsApp Business phone + 3–4 approved templates.
4. **Email provider preference** — Resend vs. SHAI's own M365 SMTP.
5. **Departments + initial user roster** — names, emails, roles to seed.
6. **Existing question bank** — CSV/JSON export from the current in-house assessment tool, if available.
7. **Existing offer letter format** — a sample to template against.
8. **Logo / brand mark** for the app header.
9. **Domain & deployment target** — decided after M0 runs locally.

---

## Risks & mitigations

- **Big-bang scope = no production value for ~3 months.** Mitigation: milestone-end demos to validate direction and re-prioritise.
- **GreytHR API unknown until we have docs.** Mitigation: M8 starts with a stub adapter; real integration when docs arrive — doesn't block other milestones.
- **WhatsApp templates need 1–3 business days for approval each.** Mitigation: submit at the start of M5, well before M9 needs them.
- **OCR accuracy on phone-shot IDs varies.** Mitigation: never auto-reject; manual-review queue for low-confidence.
- **OneDrive sync can fight `node_modules`, `.venv`, `.git`.** Mitigation: README recommends moving the repo outside OneDrive long-term.
- **Single-engineer build at risk of estimate creep.** Mitigation: explicit milestone gates; replan if M0 + M1 take >2× estimate.

---

## Non-goals for v1

- Native mobile apps (web is responsive instead).
- AI-driven candidate ranking / auto-rejection.
- Multi-tenant support (this is SHAI-only).
- LinkedIn Recruiter / Naukri RMS integration (sourcing remains manual; we capture leads, not scrape).
- Payroll, leave, performance management (lives in GreytHR).
- Background-check vendor integrations.
- Chrome extension for one-click LinkedIn add (nice-to-have, deferred).

These can be added post-v1.
