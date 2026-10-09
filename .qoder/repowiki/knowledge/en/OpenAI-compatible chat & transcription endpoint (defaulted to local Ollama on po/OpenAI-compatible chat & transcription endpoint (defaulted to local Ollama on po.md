---
kind: external_dependency
name: OpenAI-compatible chat & transcription endpoint (defaulted to local Ollama on port 11434)
slug: openai-compatible-llm-api
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
---

Both the n8n workflows and the panel's AI insights feature consume a single OpenAI-compatible HTTP API exposed at `AI_API_URL` (default `http://host.docker.internal:11434/v1/chat/completions`), authenticated via `Authorization: Bearer ${API_KEY}`. The same host/port is used for both chat completions and audio transcription (`/v1/audio/transcriptions`), which matches the Ollama server shape. The panel defaults to `gemini-2.5-flash` while n8n defaults to `gpt-4o-mini`; models are injected via environment variables. Because the URL points to `host.docker.internal`, the LLM server must run on the Docker host machine, not inside the compose network.