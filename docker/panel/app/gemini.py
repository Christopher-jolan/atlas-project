import asyncio
import logging

import httpx

from .ai_keys import gemini_api_key
from .config import AI_MODEL

log = logging.getLogger("atlas.gemini")

MODELS = [
    AI_MODEL,
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]


def _models(prefer: list[str] | None = None) -> list[str]:
    out = []
    for m in list(prefer or []) + MODELS:
        if m and ":" not in m and m not in out:
            out.append(m)
    return out or ["gemini-2.5-flash"]


def extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    chunks = []
    for p in parts:
        if p.get("text"):
            chunks.append(p["text"])
        elif isinstance(p.get("audioTranscription"), dict):
            chunks.append(p["audioTranscription"].get("text", ""))
    return "\n".join(chunks).strip()


async def gemini_text(
    payload: dict,
    timeout: int = 180,
    prefer: list[str] | None = None,
    min_len: int = 1,
) -> str:
    """Try models in order; return the first response with at least min_len chars of text."""
    api_key = gemini_api_key()
    if not api_key:
        raise RuntimeError("AI_API_KEY is empty")
    last = "no model returned text"
    async with httpx.AsyncClient(timeout=timeout) as client:
        for model in _models(prefer):
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            for attempt in range(4):
                try:
                    resp = await client.post(url, json=payload)
                except httpx.HTTPError as exc:
                    last = f"{model}: {type(exc).__name__} {exc}"
                    break
                if resp.status_code in (429, 503) and attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if resp.status_code >= 400:
                    last = f"{model}: {resp.status_code} {resp.text[:300]}"
                    if resp.status_code in (404, 400):
                        continue
                    break
                text = extract_text(resp.json())
                if len(text) >= min_len:
                    log.info("gemini %s ok (%d chars)", model, len(text))
                    return text
                last = f"{model}: short response ({len(text)} chars)"
                break
            log.warning("gemini fallback: %s", last)
    raise RuntimeError(last)
