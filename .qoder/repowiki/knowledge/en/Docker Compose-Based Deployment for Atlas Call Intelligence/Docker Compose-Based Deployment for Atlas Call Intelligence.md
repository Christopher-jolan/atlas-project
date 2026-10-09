---
kind: build_system
name: Docker Compose-Based Deployment for Atlas Call Intelligence
category: build_system
scope:
    - '**'
source_files:
    - docker/docker-compose.yml
    - docker/panel/Dockerfile
    - docker/panel/requirements.txt
    - docker/.env.example
    - docker/postgres/init/001_call_intelligence.sql
    - docker/postgres/init/002_panel_seed.sql
    - docker/n8n/workflows/atlas-call-intelligence-v1.json
    - docker/n8n/workflows/atlas-call-intelligence-monthly-report.json
    - docker/n8n/workflows/audio-analysis-workflow.json
    - docker/mailer/mailer.py
    - docker/scripts/run-test.ps1
    - docker/scripts/run-real-voice-test.py
---

## Build & Deployment Approach

This repository does not contain a traditional build system (no Makefile, no CI/CD pipeline, no package manager at the repo root). The entire operational surface is a **Docker Compose** deployment that orchestrates four services: PostgreSQL, n8n workflow engine, a Python FastAPI admin panel, and a lightweight SMTP mailer. There is no multi-stage Docker build, no cross-compilation, and no release automation — deployment is a single `docker compose up` from the `docker/` directory.

### Services and Images

- **postgres** (`postgres:16`) — persistent database with two init SQL scripts under `docker/postgres/init/` (`001_call_intelligence.sql`, `002_panel_seed.sql`). Health-checked via `pg_isready -U atlas` before dependents start.
- **n8n** (`docker.n8n.io/n8nio/n8n:latest`) — workflow orchestration; stores workflows as JSON files in `docker/n8n/workflows/` (e.g., `atlas-call-intelligence-v1.json`, `audio-analysis-workflow.json`, `double-number-workflow.json`). Credentials live in `docker/n8n/credentials/postgres.json`. Timezone set to `Asia/Tehran`.
- **mailer** (`python:3.12-slim`) — custom SMTP relay running `mailer.py`; exposed on port 8765.
- **panel** — built locally from `docker/panel/Dockerfile`; exposes FastAPI/Uvicorn on port 8080.

### Panel Application Build

The only Dockerfile in the repo is `docker/panel/Dockerfile`, which:
1. Starts from `python:3.12-slim`.
2. Installs dependencies from `docker/panel/requirements.txt` using `pip install --no-cache-dir -r requirements.txt`.
3. Copies application code (`app/`), Jinja templates (`templates/`), and static assets (`static/`).
4. Sets `PYTHONUNBUFFERED=1` and runs `uvicorn app.main:app --host 0.0.0.0 --port 8080`.

There is no version pinning of base images beyond major tags (`postgres:16`, `python:3.12-slim`, `n8nio/n8n:latest`), so builds are non-deterministic across time.

### Configuration Management

Environment variables drive all runtime configuration. A template `.env.example` lives at `docker/.env.example` and documents defaults for `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `AI_API_URL`, `TRANSCRIPTION_API_URL`, `AI_API_KEY`, `AI_MODEL`, `ATLAS_MANAGER_EMAIL`, and `ATLAS_SMTP_FROM`. Service definitions reference these via `${VAR:-default}` syntax (e.g., `AI_MODEL:${AI_MODEL:-gpt-4o-mini}`, `SMTP_HOST:${SMTP_HOST:-smtp.mail.yahoo.com}`). Hardcoded credentials exist in the compose file itself (`POSTGRES_PASSWORD: atlas123`, `DB_POSTGRESDB_PASSWORD: atlas123`, `DB_PASSWORD: atlas123`), which is a security concern for production use.

### Data Persistence

PostgreSQL data is mounted to `./postgres/data:/var/lib/postgresql/data`, making the database state persistent across container restarts. n8n workflow state persists to `./n8n/data:/home/node/.n8n`. No volumes are defined for `qdrant/` or `redis/` directories present in the tree, suggesting those services are either unused or intended to be added later.

### Testing Scripts

A small test harness lives in `docker/scripts/`:
- `run-test.ps1` — PowerShell script for running tests on Windows.
- `run-real-voice-test.py`, `send-real-call-analysis.py` — Python scripts that exercise the call analysis pipeline against real audio/transcript samples.
- `real-call-transcript.txt`, `real-call-result.json`, `test-result.json`, `test-result-final.json` — sample payloads and expected outputs used to validate the n8n workflow output format.

These are ad-hoc test fixtures rather than an automated test suite.

### SOPs

Operational procedures are documented as Markdown under `09_SOP/Deploy Docker/` and `09_SOP/Release Product/`, indicating manual runbooks exist for deployment and product releases. No automated CI/CD gates were found.

### Versioning Conventions

Version strings are embedded inside n8n workflow JSON payloads (e.g., `workflow_version: "1.0.0"` in both `atlas-call-intelligence-v1.json` and `atlas-call-intelligence-monthly-report.json`) and in the database schema (`workflow_version VARCHAR(20) DEFAULT '1.0.0'`). This tracks which workflow version produced each analysis record, but there is no external version manifest or tag-based release process visible in the repository.