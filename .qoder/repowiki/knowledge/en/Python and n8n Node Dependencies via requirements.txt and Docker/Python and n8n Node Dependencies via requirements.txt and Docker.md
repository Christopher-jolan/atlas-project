---
kind: dependency_management
name: Python and n8n Node Dependencies via requirements.txt and Docker
category: dependency_management
scope:
    - '**'
source_files:
    - docker/panel/requirements.txt
    - docker/panel/Dockerfile
    - docker/docker-compose.yml
    - docker/n8n/data/nodes/package.json
---

## What system/approach is used

This repository manages third-party dependencies using two lightweight, per-service approaches:

- **Python service (FastAPI admin panel)**: Dependencies are declared in `docker/panel/requirements.txt` with pinned versions. The panel is built into a Docker image from `python:3.12-slim`, installing packages via `pip install --no-cache-dir -r requirements.txt` during the build step.
- **n8n workflow engine**: Declared as an external Docker image (`docker.n8n.io/n8nio/n8n:latest`) in `docker/docker-compose.yml`. A minimal `package.json` under `docker/n8n/data/nodes/` exists but has no dependencies listed — it appears to be a placeholder for any future custom n8n nodes rather than an active dependency manifest.
- **Mailer helper script** (`docker/mailer/`): Uses only Python standard-library modules (`smtplib`, etc.) and declares no external dependencies.

There is no lockfile (e.g., `requirements.lock`, `Pipfile.lock`, `poetry.lock`) and no vendoring of Python packages. Dependency resolution happens at container build time against PyPI.

## Key files and packages

- `docker/panel/requirements.txt` — pins FastAPI 0.115.6, Uvicorn 0.32.1, Jinja2 3.1.4, psycopg2-binary 2.9.10, python-multipart 0.0.20, httpx 0.28.1.
- `docker/panel/Dockerfile` — builds the panel image, installs `requirements.txt`, and runs `uvicorn app.main:app` on port 8080.
- `docker/docker-compose.yml` — orchestrates four services: `postgres` (image `postgres:16`), `n8n` (image `docker.n8n.io/n8nio/n8n:latest`), `mailer` (inlined `python:3.12-slim`), and `panel` (built from `./panel`).
- `docker/n8n/data/nodes/package.json` — empty dependency list; serves as a workspace marker for potential custom n8n nodes.

## Architecture and conventions

- **Per-service manifests**: Each deployable unit owns its own dependency declaration. The panel owns `requirements.txt`; there is no shared or root-level Python dependency file.
- **Exact pinning**: All Python packages use `==` version pins in `requirements.txt`, ensuring reproducible builds without a separate lockfile.
- **Container-first installation**: Dependencies are not installed locally for development; they are installed inside the Docker image at build time. There is no virtual environment or local `pip` setup documented.
- **External services via images**: Databases (`postgres:16`) and the workflow engine (`n8n`) are pulled directly from their official registries through Docker Compose rather than being managed as code dependencies.
- **Environment-driven configuration**: Runtime secrets and endpoints are injected via environment variables (e.g., `${AI_API_KEY}`, `${SMTP_HOST}`) defined in `.env` / `.env.example` and referenced by compose, keeping credentials out of dependency manifests.

## Conventions and constraints

- **Pin every Python package with `==`** in `requirements.txt` — observed across all six entries; no loose ranges or `>=` specifiers are used.
- **No lockfile is maintained** — updates to `requirements.txt` are expected to be committed directly; reproducibility relies on exact pins rather than a generated lock.
- **Base image pinning**: The panel uses the specific `python:3.12-slim` tag, while n8n uses the rolling `latest` tag — a deliberate distinction between application runtime (pinned) and infrastructure tooling (unpinned).
- **No private registry or proxy configuration** is present in this repository; packages are resolved from the default PyPI index and official Docker registries.
- **Docker-only consumption**: There is no `setup.py`, `pyproject.toml`, or `pipenv`/`poetry` configuration; the project treats Python dependencies purely as container build inputs.