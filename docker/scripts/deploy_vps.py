#!/usr/bin/env python3
"""Upload Atlas stack to VPS and start Docker Compose. Secrets stay on the server."""
from __future__ import annotations

import os
import secrets
import stat
import sys
import time
from pathlib import Path

import paramiko

HOST = os.environ.get("ATLAS_VPS_HOST", "141.11.21.147")
PORT = int(os.environ.get("ATLAS_VPS_PORT", "9011"))
USER = os.environ.get("ATLAS_VPS_USER", "root")
PASSWORD = os.environ["ATLAS_VPS_PASSWORD"]
REMOTE = "/opt/atlas"
LOCAL_DOCKER = Path(__file__).resolve().parents[1]

SKIP_DIRS = {"postgres/data", "n8n/data", "__pycache__"}
SKIP_SUFFIXES = {".pyc", ".m4a", ".mp3", ".wav", ".ogg", ".rar"}
SKIP_NAMES = {".env", "postgres/data"}


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST,
        port=PORT,
        username=USER,
        password=PASSWORD,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
        banner_timeout=30,
    )
    return c


def run(c: paramiko.SSHClient, cmd: str, timeout: int = 300) -> str:
    print(f"\n>>> {cmd[:200]}")
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    def _safe(text: str) -> str:
        return text.encode("ascii", "replace").decode("ascii")
    if out:
        chunk = out[-4000:] if len(out) > 4000 else out
        print(_safe(chunk))
    if err:
        chunk = err[-2000:] if len(err) > 2000 else err
        print(_safe(chunk))
    if code != 0:
        raise SystemExit(f"remote command failed ({code}): {cmd}")
    return out


def should_skip(rel: Path) -> bool:
    parts = rel.as_posix()
    if any(parts.startswith(d) or f"/{d}/" in f"/{parts}/" for d in SKIP_DIRS):
        if parts.startswith("postgres/init") or parts.startswith("n8n/workflows"):
            return False
        if parts.startswith("postgres/data") or parts.startswith("n8n/data"):
            return True
    if rel.suffix.lower() in SKIP_SUFFIXES:
        return True
    if rel.name in {".env"}:
        return True
    if "__pycache__" in rel.parts:
        return True
    return False


def upload_tree(sftp: paramiko.SFTPClient, local: Path, remote: str) -> None:
    def mkdir_p(path: str) -> None:
        dirs = []
        while path not in ("", "/"):
            dirs.append(path)
            path = str(Path(path).parent).replace("\\", "/")
        for d in reversed(dirs):
            try:
                sftp.stat(d)
            except FileNotFoundError:
                sftp.mkdir(d)

    mkdir_p(remote)
    for root, dirs, files in os.walk(local):
        root_p = Path(root)
        rel_dir = root_p.relative_to(local)
        dirs[:] = [d for d in dirs if d not in {"data", "__pycache__"} or rel_dir.as_posix() not in {"postgres", "n8n"}]
        if rel_dir.as_posix() in {"postgres", "n8n"}:
            dirs[:] = [d for d in dirs if d != "data"]
        rdir = f"{remote}/{rel_dir.as_posix()}" if rel_dir.as_posix() != "." else remote
        mkdir_p(rdir)
        for name in files:
            rel = (rel_dir / name) if rel_dir.as_posix() != "." else Path(name)
            if should_skip(rel):
                continue
            lp = root_p / name
            rp = f"{rdir}/{name}"
            print(f"upload {rel.as_posix()}")
            sftp.put(str(lp), rp)


def main() -> None:
    c = connect()
    sftp = c.open_sftp()
    print("connected")

    run(c, "mkdir -p /opt/atlas /opt/atlas/postgres/init /opt/atlas/n8n/workflows /opt/atlas/n8n/data /opt/atlas/postgres/data")
    sftp.put(str(LOCAL_DOCKER / "scripts" / "remote_bootstrap.sh"), "/tmp/remote_bootstrap.sh")
    run(c, "sed -i 's/\\r$//' /tmp/remote_bootstrap.sh && chmod +x /tmp/remote_bootstrap.sh && bash /tmp/remote_bootstrap.sh", timeout=400)

    upload_tree(sftp, LOCAL_DOCKER, REMOTE)

    env_path = f"{REMOTE}/.env"
    try:
        sftp.stat(env_path)
        print(".env exists, keeping it")
    except FileNotFoundError:
        pg = secrets.token_urlsafe(18)
        n8n = secrets.token_urlsafe(18)
        panel = secrets.token_urlsafe(12)
        api = secrets.token_urlsafe(24)
        env = f"""POSTGRES_USER=atlas
POSTGRES_PASSWORD={pg}
POSTGRES_DB=atlas
N8N_USER=admin
N8N_PASSWORD={n8n}
N8N_HOST=141.11.21.147
WEBHOOK_URL=http://141.11.21.147:5678/
PANEL_PASSWORD={panel}
API_TOKEN={api}
PANEL_TITLE=پنل مدیریت اطلس
AI_API_KEY=
AI_MODEL=gemini-2.5-flash
AI_API_URL=
TRANSCRIPTION_API_URL=
ATLAS_MANAGER_EMAIL=
ATLAS_SMTP_FROM=
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
UPLOAD_MAX_MB=25
"""
        with sftp.file(env_path, "w") as f:
            f.write(env)
        sftp.chmod(env_path, 0o600)
        creds = (
            "Atlas VPS credentials (server-only)\n"
            f"Panel: http://141.11.21.147/  password: {panel}\n"
            f"n8n:   http://141.11.21.147:5678/  user: admin  password: {n8n}\n"
            f"API token header X-API-Token: {api}\n"
            f"Postgres user atlas password: {pg}\n"
        )
        with sftp.file("/root/atlas-credentials.txt", "w") as f:
            f.write(creds)
        sftp.chmod("/root/atlas-credentials.txt", 0o600)
        print(creds)

    run(
        c,
        "cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build",
        timeout=600,
    )
    time.sleep(8)
    run(c, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
    run(c, "curl -sS -o /dev/null -w 'panel80:%{http_code}\\n' http://127.0.0.1/login || true")
    run(c, "curl -sS -o /dev/null -w 'n8n:%{http_code}\\n' http://127.0.0.1:5678/healthz || true")
    sftp.close()
    c.close()
    print("done")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAILED:", exc, file=sys.stderr)
        sys.exit(1)
