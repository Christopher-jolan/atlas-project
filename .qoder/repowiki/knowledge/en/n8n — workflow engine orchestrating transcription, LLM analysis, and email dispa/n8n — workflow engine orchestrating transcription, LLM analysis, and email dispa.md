---
kind: external_dependency
name: n8n — workflow engine orchestrating transcription, LLM analysis, and email dispatch
slug: n8n
category: external_dependency
category_hints:
    - vendor_identity
    - framework_behavior
scope:
    - '**'
---

n8n (docker.n8n.io/n8nio/n8n:latest) is the integration layer between incoming audio/transcript payloads and the rest of the system. A webhook node accepts POST requests, optionally calls a local OpenAI-compatible transcription endpoint (`TRANSCRIPTION_API_URL`, defaulting to host.docker.internal:11434/v1/audio/transcriptions), builds a structured prompt, then calls an OpenAI-compatible chat completion endpoint (`API_URL`, model `gpt-4o-mini` by default) to produce per-call analysis JSON. The current v5 workflow shown in the repo emits the analysis but does not persist it to PostgreSQL or send email without additional nodes; the conversation identified this gap and described adding a 'Save to DB' node plus a 'Forward Data' node before the mailer. Multiple workflow versions exist under `docker/n8n/workflows/` (audio-analysis-advanced-v2..v5, monthly-report, double-number variants). Timezone is set to Asia/Tehran.