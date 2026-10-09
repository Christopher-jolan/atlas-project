import psycopg2
import psycopg2.extras
from contextlib import contextmanager

from .config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def get_dsn() -> str:
    return f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"


@contextmanager
def get_conn():
    conn = psycopg2.connect(get_dsn())
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(query: str, params=None) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or ())
            return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params=None) -> dict | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def execute(query: str, params=None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
        conn.commit()
