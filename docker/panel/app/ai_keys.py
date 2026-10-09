"""Resolve Gemini API key: container env first, then panel_settings (admin UI)."""
import os
import time

from . import queries

_cache: dict = {"at": 0.0, "key": ""}


def gemini_api_key() -> str:
    env_key = (os.getenv("AI_API_KEY") or "").strip()
    if env_key:
        return env_key
    if time.time() - _cache["at"] < 15 and _cache["key"]:
        return _cache["key"]
    row = queries.get_settings().get("gemini_api_key", "")
    key = (row or "").strip()
    _cache["at"] = time.time()
    _cache["key"] = key
    return key


def invalidate_cache() -> None:
    _cache["at"] = 0.0
    _cache["key"] = ""
