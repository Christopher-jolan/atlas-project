"""User accounts and HMAC-signed session cookies."""
import base64
import hashlib
import hmac
import secrets
import time
from functools import lru_cache

from .db import execute, fetch_all, fetch_one

COOKIE_NAME = "atlas_session"
REMEMBER_SECONDS = 30 * 86400
SESSION_SECONDS = 12 * 3600
ROLES = {"admin": "مدیر سیستم", "manager": "مدیر", "viewer": "مشاهده‌گر"}
_PBKDF2_ROUNDS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return "pbkdf2${}${}${}".format(
        _PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$")
        expected = base64.b64decode(digest)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


@lru_cache(maxsize=1)
def _secret() -> bytes:
    row = fetch_one("SELECT value FROM panel_settings WHERE key = 'session_secret'")
    return row["value"].encode()


def _fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:12]


def _sign(payload: str) -> str:
    return hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()


def make_session(user: dict, remember: bool) -> tuple[str, int | None]:
    ttl = REMEMBER_SECONDS if remember else SESSION_SECONDS
    payload = f"{user['id']}.{int(time.time()) + ttl}.{_fingerprint(user['password_hash'])}"
    return f"{payload}.{_sign(payload)}", (ttl if remember else None)


def user_from_session(token: str | None) -> dict | None:
    if not token or token.count(".") != 3:
        return None
    uid, exp, fp, sig = token.split(".")
    if not hmac.compare_digest(sig, _sign(f"{uid}.{exp}.{fp}")):
        return None
    if not exp.isdigit() or int(exp) < time.time() or not uid.isdigit():
        return None
    user = get_user(int(uid))
    if not user or not user["is_active"] or _fingerprint(user["password_hash"]) != fp:
        return None
    return user


def authenticate(username: str, password: str) -> dict | None:
    user = fetch_one(
        "SELECT * FROM users WHERE lower(username) = lower(%s) AND is_active", (username.strip(),)
    )
    if user and verify_password(password, user["password_hash"]):
        execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user["id"],))
        return user
    return None


def get_user(user_id: int) -> dict | None:
    return fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))


def list_users() -> list[dict]:
    return fetch_all(
        "SELECT id, username, full_name, role, is_active, created_at, last_login_at FROM users ORDER BY id"
    )


def create_user(username: str, full_name: str, password: str, role: str) -> None:
    execute(
        "INSERT INTO users (username, full_name, password_hash, role) VALUES (%s, %s, %s, %s)",
        (username.strip(), full_name.strip(), hash_password(password), role),
    )


def set_password(user_id: int, password: str) -> None:
    execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(password), user_id))


def set_active(user_id: int, active: bool) -> None:
    execute("UPDATE users SET is_active = %s WHERE id = %s", (active, user_id))


def delete_user(user_id: int) -> None:
    execute("DELETE FROM users WHERE id = %s", (user_id,))


def can(user: dict | None, action: str) -> bool:
    if not user:
        return False
    role = user["role"]
    if action == "admin":
        return role == "admin"
    if action == "upload":
        return role in ("admin", "manager")
    return True
