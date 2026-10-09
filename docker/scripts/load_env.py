"""Load docker/.env into os.environ without overriding existing variables."""
from __future__ import annotations

import os
from pathlib import Path

_DOCKER_DIR = Path(__file__).resolve().parents[1]
_ENV_FILE = _DOCKER_DIR / ".env"


def load_docker_env() -> None:
    if not _ENV_FILE.is_file():
        return
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
