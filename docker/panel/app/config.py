import os

from .env_loader import load_docker_env

load_docker_env()

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "atlas")
DB_USER = os.getenv("DB_USER", "atlas")
DB_PASSWORD = os.getenv("DB_PASSWORD", "atlas123")

AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

PANEL_TITLE = os.getenv("PANEL_TITLE", "پنل مدیریت اطلس")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_COMPANY_NAME = os.getenv("COMPANY_NAME", "اطلس")
DEFAULT_BUSINESS_CONTEXT = os.getenv("BUSINESS_CONTEXT", "")
PANEL_PUBLIC_URL = os.getenv("PANEL_PUBLIC_URL", "").rstrip("/")

N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://n8n:5678/webhook/atlas/call-intelligence",
)
TRANSCRIPTION_API_URL = os.getenv(
    "TRANSCRIPTION_API_URL",
    "http://host.docker.internal:11434/v1/audio/transcriptions",
)
MAILER_URL = os.getenv("MAILER_URL", "http://mailer:8765")
UPLOAD_MAX_MB = int(os.getenv("UPLOAD_MAX_MB", "25"))

API_TOKEN = os.getenv("API_TOKEN", "")
PUBLIC_DEMO_API = os.getenv("PUBLIC_DEMO_API", "true").lower() in ("1", "true", "yes")
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "30"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
