"""Idempotent schema setup run at panel startup (init SQL only runs on a fresh volume)."""
import logging
import os
import secrets

from .config import PANEL_PASSWORD, ADMIN_USERNAME, DEFAULT_BUSINESS_CONTEXT, DEFAULT_COMPANY_NAME
from .db import execute, fetch_one

log = logging.getLogger("atlas.migrations")

DEFAULT_SETTINGS = {
    "company_name": DEFAULT_COMPANY_NAME,
    "company_tagline": "هوش تماس و تحلیل مکالمات",
    "business_context": DEFAULT_BUSINESS_CONTEXT,
    "brand_color": "#4f46e5",
    "logo_url": "",
    "notify_emails": os.getenv("ATLAS_MANAGER_EMAIL", ""),
    "notify_mode": "all",
    "alert_cooldown_minutes": "60",
    "sms_enabled": "true",
    "sms_provider": os.getenv("SMS_PROVIDER", "iransms"),
    "sms_username": os.getenv("SMS_USERNAME", ""),
    "sms_password": os.getenv("SMS_PASSWORD", ""),
    "sms_api_key": os.getenv("GHASEDAK_API_KEY", ""),
    "sms_line_number": os.getenv("SMS_LINE_NUMBER", "2170003727"),
    "sms_manager_numbers": os.getenv("SMS_MANAGER_NUMBERS", ""),
    "sms_manager_mode": "all",
    "sms_customer_enabled": "true",
    "sms_customer_text": os.getenv(
        "SMS_CUSTOMER_TEXT",
        "گروه نرم افزاری اطلس\nهوشمند تر کار کن سریع تر رشد کن\nبا سپاس از حسن انتخاب شما",
    ),
    "gemini_api_key": "",
}


def run() -> None:
    execute("""
        CREATE TABLE IF NOT EXISTS panel_settings (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            full_name VARCHAR(200) NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'viewer',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_login_at TIMESTAMPTZ
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS sms_log (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            kind VARCHAR(20) NOT NULL,
            receptor VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            message_id VARCHAR(64) DEFAULT '',
            error TEXT DEFAULT '',
            call_id VARCHAR(255)
        )
    """)
    execute("CREATE INDEX IF NOT EXISTS idx_sms_log_receptor ON sms_log (receptor, kind, created_at)")

    for key, value in DEFAULT_SETTINGS.items():
        execute(
            "INSERT INTO panel_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
            (key, value),
        )

    legacy = fetch_one("SELECT value FROM panel_settings WHERE key = 'manager_email'")
    current = fetch_one("SELECT value FROM panel_settings WHERE key = 'notify_emails'")
    if legacy and legacy["value"] and current and not current["value"]:
        execute("UPDATE panel_settings SET value = %s WHERE key = 'notify_emails'", (legacy["value"],))

    env_gemini = (os.getenv("AI_API_KEY") or "").strip()
    gem_row = fetch_one("SELECT value FROM panel_settings WHERE key = 'gemini_api_key'")
    if env_gemini and gem_row and not (gem_row["value"] or "").strip():
        execute("UPDATE panel_settings SET value = %s WHERE key = 'gemini_api_key'", (env_gemini,))

    if not fetch_one("SELECT value FROM panel_settings WHERE key = 'session_secret'"):
        execute(
            "INSERT INTO panel_settings (key, value) VALUES ('session_secret', %s)",
            (secrets.token_hex(32),),
        )

    if not fetch_one("SELECT id FROM users LIMIT 1"):
        from .auth import hash_password

        password = PANEL_PASSWORD or secrets.token_urlsafe(12)
        execute(
            "INSERT INTO users (username, full_name, password_hash, role) VALUES (%s, %s, %s, 'admin')",
            (ADMIN_USERNAME, "مدیر سیستم", hash_password(password)),
        )
        if not PANEL_PASSWORD:
            log.warning("Created admin user %r with generated password: %s", ADMIN_USERNAME, password)
