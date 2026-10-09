---
kind: configuration_system
name: Docker-Compose + Environment Variables Configuration System
category: configuration_system
scope:
    - '**'
source_files:
    - docker/.env.example
    - docker/docker-compose.yml
    - docker/panel/app/config.py
    - docker/mailer/mailer.py
    - docker/n8n/credentials/postgres.json
---

## What system/approach is used

The repository uses a **Docker Compose–based configuration system** centered on environment variables. There is no centralized config file parser, YAML/JSON config loader, or feature-flag framework. Instead, every runtime service (PostgreSQL, n8n, the Python mailer, and the FastAPI admin panel) is configured exclusively through `docker-compose.yml` `environment:` blocks that map `.env` values into container processes via `os.getenv()`.

## Key files and packages

- `docker/.env.example` — template of all configurable keys with defaults; the canonical reference for what can be overridden at deploy time.
- `docker/docker-compose.yml` — single source of truth for service definitions, port mappings, volumes, health checks, and environment variable injection per service.
- `docker/panel/app/config.py` — Panel application reads its own subset of env vars (`DB_*`, `AI_API_KEY`, `AI_MODEL`, `PANEL_TITLE`, `PANEL_PASSWORD`) via `os.getenv` with built-in defaults.
- `docker/mailer/mailer.py` — standalone HTTP mailer reads SMTP credentials and target email from `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `ATLAS_MANAGER_EMAIL`, `MAILER_PORT`.
- `docker/n8n/credentials/postgres.json` — n8n's internal credential store for PostgreSQL (host, database, user, password, port, ssl); this is the only non-env configuration artifact in the stack.
- `docker/postgres/init/*.sql` — database schema and seed data loaded once by PostgreSQL's entrypoint.

## Architecture and conventions

1. **Single `.env` file drives the whole stack.** `docker-compose.yml` references values via `${VAR}` syntax (e.g. `${AI_API_URL}`, `${AI_API_KEY}`, `${ATLAS_MANAGER_EMAIL}`). The `.env.example` file documents every key; developers copy it to `.env` and fill in secrets.
2. **Per-service environment scoping.** Each service declares exactly the env vars it needs:
   - `postgres`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (hardcoded in compose, not from `.env`).
   - `n8n`: DB connection, timezone, AI API endpoints/keys, manager email, plus `N8N_SECURE_COOKIE` and `N8N_BLOCK_ENV_ACCESS_IN_NODE` toggles.
   - `mailer`: SMTP host/port/user/pass, default recipient, listening port.
   - `panel`: DB connection, AI model/key, UI title, optional admin password.
3. **Defaults are provided inline in two places.** `docker-compose.yml` uses `${VAR:-default}` syntax (e.g. `AI_MODEL:-gpt-4o-mini`, `PANEL_TITLE:-پنل مدیریت اطلس`). Application code also supplies fallback defaults via `os.getenv("KEY", "default")` (e.g. `DB_HOST="postgres"`, `AI_MODEL="gemini-2.5-flash"`). This means services start even if `.env` is missing, but behavior may differ from intended.
4. **Secrets are treated as plain env vars.** No secret manager, no encrypted vault, no `.env` exclusion beyond `.gitignore`. Credentials (DB passwords, SMTP pass, AI keys) live in `.env` and are committed as examples in `.env.example` with placeholder values.
5. **n8n credentials are stored as JSON.** The PostgreSQL credential for n8n workflows lives in `docker/n8n/credentials/postgres.json` and is mounted into the n8n container under `/home/node/.n8n`; it is not sourced from env vars.
6. **No layered configuration.** There is no concept of dev/staging/prod overrides, no config merging, no hot reload. Changing configuration requires editing `.env` (or compose `environment:`) and restarting containers.
7. **Feature toggles are absent.** Behavior is controlled entirely by presence/value of env vars (e.g. `PANEL_PASSWORD` enables simple auth when set; `ATLAS_MANAGER_EMAIL` enables ticket emails). There is no typed feature-flag registry.

## Conventions and constraints

- Every configurable value has a documented name in `docker/.env.example`; new settings should be added there first.
- Service-to-service communication uses Docker DNS names (`postgres`, `n8n`) rather than `localhost`; external dependencies (AI APIs) use `host.docker.internal` URLs pointing at the host machine.
- Database credentials for PostgreSQL are hardcoded directly in `docker-compose.yml` `environment:` blocks (not pulled from `.env`), while the `panel` service reads them from its own env var set — a slight inconsistency worth noting.
- The `mailer` service enforces that `SMTP_PASS` must be set; sending fails with an explicit error otherwise, making it a required secret.
- Timezone is consistently set to `Asia/Tehran` via both `GENERIC_TIMEZONE` and `TZ` env vars across services that need it.