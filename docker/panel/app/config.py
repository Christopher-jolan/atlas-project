import os

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "atlas")
DB_USER = os.getenv("DB_USER", "atlas")
DB_PASSWORD = os.getenv("DB_PASSWORD", "atlas123")

AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

PANEL_TITLE = os.getenv("PANEL_TITLE", "پنل مدیریت اطلس")
# Initial password for the bootstrap admin account (only used when the users table is empty).
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

# Token for server-to-server API access (header X-API-Token); empty = disabled.
API_TOKEN = os.getenv("API_TOKEN", "")
# Lets an external showcase site call stats/upload endpoints without logging in.
PUBLIC_DEMO_API = os.getenv("PUBLIC_DEMO_API", "true").lower() in ("1", "true", "yes")

# Requests per minute per IP for upload endpoints.
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "30"))

# CORS allowed origins (comma-separated, * = all)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
