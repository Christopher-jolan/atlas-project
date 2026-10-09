---
kind: external_dependency
name: PostgreSQL — persistent store for call analyses and monthly reports
slug: postgresql
category: external_dependency
category_hints:
    - vendor_identity
scope:
    - '**'
---

PostgreSQL 16 is the sole persistent data store for Atlas Call Intelligence. It runs as a Docker service (`atlas-postgres`) with database `atlas`, user `atlas`. The panel (FastAPI) connects via `psycopg2-binary` using env vars `DB_HOST/PORT/NAME/USER/PASSWORD`. n8n also uses this same Postgres instance for its own workflow state (configured via `DB_TYPE=postgresdb`). Schema lives in `docker/postgres/init/001_call_intelligence.sql` and defines two tables: `call_analyses` (per-call AI analysis, JSONB payload, scores, flags) and `monthly_reports` (aggregated monthly summaries). All panel report pages read from these tables; the conversation revealed that the n8n workflow must be configured to write results into `call_analyses` so the panel has data to display.