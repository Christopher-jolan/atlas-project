"""Load docker/.env for local runs (file is gitignored; containers use real env vars)."""
import os
from pathlib import Path

_DOCKER_ENV = Path(__file__).resolve().parents[2] / ".env"


def load_docker_env() -> None:
    if not _DOCKER_ENV.is_file():
        return
    for line in _DOCKER_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
