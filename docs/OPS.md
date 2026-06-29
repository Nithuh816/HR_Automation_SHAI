# Operations Runbook — HR_Automation_SHAI

Production is a single Docker Compose stack (`docker-compose.prod.yml`): Caddy
(TLS edge + SPA) → FastAPI (`--workers 4`) → PostgreSQL + Redis, plus a Celery
`worker` and `beat`. The same images run on any VM or PaaS.

```
Internet ──TLS──> Caddy (web) ──/api──> api (uvicorn x4) ──> postgres
                    │                       │          └──> redis ──> worker + beat
                    └── serves built SPA    └──> S3 (R2/MinIO), SMTP, MS Graph, GreytHR, WhatsApp
```

## 1. Prerequisites
- A host with Docker Engine + Compose v2.
- DNS A/AAAA record pointing your domain at the host (for automatic HTTPS).
- A `.env` file on the host (never committed). Start from `.env.example`.

## 2. First deploy
```bash
cp .env.example .env          # then edit — see §3
docker compose -f docker-compose.prod.yml up -d --build
# create the schema (one-off; NOT run automatically on container start):
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
# seed departments + staff (idempotent; safe to re-run):
docker compose -f docker-compose.prod.yml exec api python -m app.seed
```
Open `https://<SITE_ADDRESS>` — health is at `https://<SITE_ADDRESS>/health`.

## 3. Required `.env` values
| Var | Notes |
| --- | --- |
| `SITE_ADDRESS` | Domain for HTTPS (e.g. `hr.shaihealth.com`), or `:80` for HTTP. |
| `POSTGRES_PASSWORD` | Required — compose refuses to start without it. |
| `APP_SECRET_KEY` | JWT signing key. Generate: `openssl rand -hex 32`. |
| `PII_ENC_KEY` | Fernet key for Aadhaar/PAN/bank columns. Generate: `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`. |
| `MAGIC_LINK_HMAC_KEY` | Candidate-link signing key. `openssl rand -hex 32`. |
| `STORAGE_BACKEND` + `S3_*` | `r2`/`s3`/`minio` plus endpoint/keys/bucket for document storage. |
| `EMAIL_PROVIDER` + SMTP/Resend | `smtp` (M365) or `resend`; sets how candidate email is sent. |
| `MS_*` | Microsoft Entra ID app (SSO + Teams). Until set, only dev-login works. |
| `GREYTHR_*` | Onboarding handoff. Until set, a deterministic stub adapter is used. |
| `WHATSAPP_*` | WhatsApp Cloud API. Until set, a no-op stub is used. |
| `RETENTION_DAYS` | DPDPA purge window for rejected candidates (default `365`). |

> Secrets live only in `.env` (root-owned, `chmod 600`) or your secret manager. Rotate `PII_ENC_KEY` annually; rotating it requires re-encrypting stored columns.

## 4. Scheduled jobs (Celery beat)
The `beat` container schedules, `worker` executes. All tasks are idempotent.
| Task | Cadence | Purpose |
| --- | --- | --- |
| `outbox.deliver` | 60s | Send queued email/WhatsApp. |
| `assessment.expire_attempts` | 5m | Close timed-out L2 attempts. |
| `reminders.interviews` | 15m | Email candidates with interviews in the next 24h. |
| `reminders.day_before_joining` | 1h | Day-before joining confirmation. |
| `sla.check_requisitions` | 1h | Flag requisitions past their due date to the HR Head. |
| `retention.purge_rejected` | 24h | Anonymise rejected-candidate PII older than `RETENTION_DAYS`. |

Inspect: `docker compose -f docker-compose.prod.yml logs -f worker beat`.
Email outbox can be flushed on demand by the HR Head via `POST /api/v1/notifications/flush`.

## 5. Upgrades
```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```
Migrations are forward-only in practice; verify on a staging copy first. To roll
a migration back: `alembic downgrade -1`.

## 6. Backups & restore
```bash
# Backup (cron daily, ship off-host):
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U hr hr_automation | gzip > backup-$(date +%F).sql.gz
# Restore into an empty DB:
gunzip -c backup-YYYY-MM-DD.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres psql -U hr hr_automation
```
Also back up the object-storage bucket (uploaded documents) and `.env`.

## 7. Scaling & health
- API throughput: raise `--workers`, or `docker compose ... up -d --scale api=N` behind Caddy.
- Job throughput: `--scale worker=N` (keep exactly **one** `beat`).
- Liveness: `GET /health`. Container healthchecks gate `postgres`/`redis` startup.

## 8. Rollback
```bash
git checkout <previous-tag>
docker compose -f docker-compose.prod.yml up -d --build
# only if that release changed the schema and you must revert it:
docker compose -f docker-compose.prod.yml exec api alembic downgrade <prev_revision>
```

## 9. Security posture (operational)
- Internal access: Microsoft 365 SSO + RBAC. Dev-login is disabled when `APP_ENV=production`.
- Candidate access: single-use, scoped, HMAC-bound magic links.
- PII at rest: Aadhaar/PAN/bank encrypted (Fernet); documents in object storage, served only via short-lived links.
- DPDPA: consent captured + timestamped on candidate pages; rejected-candidate PII purged after `RETENTION_DAYS`.
- Report security issues privately to the repo owner.
