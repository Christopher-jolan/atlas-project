# Getting Started

<cite>
**Referenced Files in This Document**
- [docker-compose.yml](file://docker/docker-compose.yml)
- [config.py](file://docker/panel/app/config.py)
- [main.py](file://docker/panel/app/main.py)
- [db.py](file://docker/panel/app/db.py)
- [001_call_intelligence.sql](file://docker/postgres/init/001_call_intelligence.sql)
- [002_panel_seed.sql](file://docker/postgres/init/002_panel_seed.sql)
- [mailer.py](file://docker/mailer/mailer.py)
- [Dockerfile](file://docker/panel/Dockerfile)
- [requirements.txt](file://docker/panel/requirements.txt)
</cite>

## Table of Contents
1. Introduction
2. Prerequisites
3. Quick Start with Docker Compose
4. Environment Variables Reference
5. First Run and Default Credentials
6. Verify Services Are Running
7. Basic Configuration Steps
8. Troubleshooting Common Issues
9. Next Steps

## Introduction
This guide helps you get Atlas running quickly using Docker Compose. Atlas includes:
- PostgreSQL database with initialization scripts
- n8n workflow automation service
- A Python-based Manager Panel (FastAPI) for call analytics and reporting
- A lightweight mailer service for sending notifications via SMTP

You will start all services, set required environment variables, and verify that the panel and other components are healthy.

## Prerequisites
- Docker and Docker Compose installed on your machine
- Sufficient disk space for container images and data volumes
- Optional but recommended: a local .env file to manage secrets and endpoints

## Quick Start with Docker Compose
1. Navigate to the docker directory:
   - cd docker
2. Create an environment file if you do not have one:
   - cp ../.env.example .env  # if available; otherwise create a new .env
3. Start all services:
   - docker compose up -d
4. Wait for services to become healthy:
   - Check logs: docker compose logs -f
   - Ensure PostgreSQL is ready before n8n and panel connect

Services exposed by default:
- PostgreSQL: port 5432
- n8n: port 5678
- Panel: port 8080
- Mailer: port 8765

**Section sources**
- [docker-compose.yml:1-98](file://docker/docker-compose.yml#L1-L98)
- [Dockerfile:1-11](file://docker/panel/Dockerfile#L1-L11)

## Environment Variables Reference
Atlas uses environment variables to configure integrations and behavior. The following are essential or commonly used:

- AI integration (used by n8n and panel):
  - AI_API_URL
  - TRANSCRIPTION_API_URL
  - AI_API_KEY
  - AI_MODEL (defaults vary per service)

- Email (mailer service):
  - SMTP_HOST
  - SMTP_PORT
  - SMTP_USER
  - SMTP_PASS
  - ATLAS_MANAGER_EMAIL
  - MAILER_PORT

- Panel authentication:
  - PANEL_PASSWORD (optional simple password protection)

- Panel display:
  - PANEL_TITLE

Notes:
- If PANEL_PASSWORD is empty, the panel skips login and redirects to the dashboard.
- If PANEL_PASSWORD is set, access requires submitting the correct password once per session.

**Section sources**
- [docker-compose.yml:26-57](file://docker/docker-compose.yml#L26-L57)
- [docker-compose.yml:62-79](file://docker/docker-compose.yml#L62-L79)
- [docker-compose.yml:80-98](file://docker/docker-compose.yml#L80-L98)
- [config.py:1-14](file://docker/panel/app/config.py#L1-L14)
- [main.py:40-65](file://docker/panel/app/main.py#L40-L65)
- [mailer.py:10-15](file://docker/mailer/mailer.py#L10-L15)

## First Run and Default Credentials
- Database credentials (PostgreSQL):
  - User: atlas
  - Password: atlas123
  - Database: atlas
  - Host: localhost (port 5432)

- Panel:
  - URL: http://localhost:8080
  - If PANEL_PASSWORD is set, use it at /login
  - If PANEL_PASSWORD is not set, you are redirected directly to the dashboard

- n8n:
  - URL: http://localhost:5678

- Mailer:
  - HTTP endpoint: http://localhost:8765/send

Important:
- These defaults are defined in the compose configuration. For production, override them via environment variables and secure storage.

**Section sources**
- [docker-compose.yml:3-25](file://docker/docker-compose.yml#L3-L25)
- [docker-compose.yml:80-98](file://docker/docker-compose.yml#L80-L98)
- [main.py:40-65](file://docker/panel/app/main.py#L40-L65)

## Verify Services Are Running
Use these checks after starting the stack:

- Health check PostgreSQL:
  - docker exec atlas-postgres pg_isready -U atlas

- Access the Panel:
  - Open http://localhost:8080
  - If PANEL_PASSWORD is configured, log in at /login

- Access n8n:
  - Open http://localhost:5678

- Test the mailer:
  - curl -X POST http://localhost:8765/send -H "Content-Type: application/json" -d '{"to":"your@email.com","subject":"Test","body":"Hello"}'

Optional: Seed sample data into the database to explore the panel:
- docker exec -i atlas-postgres psql -U atlas -d atlas < docker/postgres/init/002_panel_seed.sql

**Section sources**
- [docker-compose.yml:20-25](file://docker/docker-compose.yml#L20-L25)
- [docker-compose.yml:80-98](file://docker/docker-compose.yml#L80-L98)
- [002_panel_seed.sql:1-46](file://docker/postgres/init/002_panel_seed.sql#L1-L46)

## Basic Configuration Steps
1. Configure AI integrations:
   - Set AI_API_URL, TRANSCRIPTION_API_URL, AI_API_KEY, and optionally AI_MODEL in your environment.
   - These values are consumed by n8n and the panel when generating insights.

2. Configure email:
   - Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, and ATLAS_MANAGER_EMAIL.
   - The mailer listens on port 8765 and sends emails via the configured SMTP server.

3. Secure the panel:
   - Set PANEL_PASSWORD to enable simple login.
   - Optionally customize PANEL_TITLE for branding.

4. Persist data:
   - PostgreSQL data is mounted under docker/postgres/data.
   - n8n data is mounted under docker/n8n/data.

5. Timezone and locale:
   - n8n uses GENERIC_TIMEZONE and TZ; adjust as needed.

**Section sources**
- [docker-compose.yml:26-57](file://docker/docker-compose.yml#L26-L57)
- [docker-compose.yml:62-79](file://docker/docker-compose.yml#L62-L79)
- [docker-compose.yml:80-98](file://docker/docker-compose.yml#L80-L98)
- [config.py:1-14](file://docker/panel/app/config.py#L1-L14)
- [mailer.py:10-15](file://docker/mailer/mailer.py#L10-L15)

## Troubleshooting Common Issues
- Cannot connect to PostgreSQL:
  - Ensure the container is healthy and ports are not conflicting.
  - Verify DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD match your environment.
  - Confirm init scripts ran successfully.

- Panel shows login loop or redirects unexpectedly:
  - If PANEL_PASSWORD is empty, the panel bypasses login.
  - If PANEL_PASSWORD is set, ensure you submit the correct value at /login.

- n8n cannot connect to the database:
  - Check DB_* environment variables for n8n.
  - Ensure PostgreSQL is healthy before n8n starts.

- Emails not sending:
  - Validate SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
  - Check mailer logs and test the /send endpoint.

- Panel fails to build or run:
  - Ensure dependencies in requirements.txt are installable.
  - Rebuild the panel image if you change code or dependencies.

- Port conflicts:
  - Change exposed ports in docker-compose.yml if another service uses 5432, 5678, 8080, or 8765.

**Section sources**
- [docker-compose.yml:3-25](file://docker/docker-compose.yml#L3-L25)
- [docker-compose.yml:26-57](file://docker/docker-compose.yml#L26-L57)
- [docker-compose.yml:62-79](file://docker/docker-compose.yml#L62-L79)
- [docker-compose.yml:80-98](file://docker/docker-compose.yml#L80-L98)
- [db.py:1-31](file://docker/panel/app/db.py#L1-L31)
- [mailer.py:18-33](file://docker/mailer/mailer.py#L18-L33)
- [requirements.txt:1-7](file://docker/panel/requirements.txt#L1-L7)

## Next Steps
- Explore the Manager Panel dashboards for call analytics and monthly reports.
- Use n8n to automate workflows that ingest call data and trigger notifications.
- Customize templates and styles in the panel static assets and Jinja templates.
- Add additional Postgres migrations under docker/postgres/init as your schema evolves.