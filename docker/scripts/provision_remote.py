#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import secrets
import sys
import time
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = os.environ.get("ATLAS_VPS_HOST", "141.11.21.147")
PORT = int(os.environ.get("ATLAS_VPS_PORT", "9011"))
USER = os.environ.get("ATLAS_VPS_USER", "root")
PASSWORD = os.environ["ATLAS_VPS_PASSWORD"]
REMOTE = "/opt/atlas"
LOCAL_DOCKER = Path(__file__).resolve().parents[1]
GEMINI_KEY = os.environ.get("ATLAS_GEMINI_KEY", "")
SMTP_USER = os.environ.get("ATLAS_SMTP_USER", "mohamad.j1380@yahoo.com")
SMTP_PASS = os.environ.get("ATLAS_SMTP_PASS", "")
ADMIN_PASS = os.environ.get("ATLAS_ADMIN_PASS") or ("At!as-" + secrets.token_urlsafe(10))


def connect() -> paramiko.SSHClient:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(
        HOST, port=PORT, username=USER, password=PASSWORD,
        timeout=30, allow_agent=False, look_for_keys=False, banner_timeout=30,
    )
    return c


def run(c: paramiko.SSHClient, cmd: str, timeout: int = 300) -> str:
    print(">>>", cmd[:180].replace("\n", " "))
    _, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    if out:
        print(out[-3500:] if len(out) > 3500 else out)
    if err and code != 0:
        print(err[-2000:] if len(err) > 2000 else err)
    if code != 0:
        raise SystemExit(f"failed ({code}): {cmd[:120]}")
    return out


def mkdir_p(sftp, path: str) -> None:
    dirs = []
    while path not in ("", "/"):
        dirs.append(path)
        path = str(Path(path).parent).replace("\\", "/")
    for d in reversed(dirs):
        try:
            sftp.stat(d)
        except FileNotFoundError:
            sftp.mkdir(d)


def upload_tree(sftp, local: Path, remote: str) -> None:
    mkdir_p(sftp, remote)
    for root, dirs, files in os.walk(local):
        root_p = Path(root)
        rel_dir = root_p.relative_to(local)
        posix = rel_dir.as_posix()
        if posix in {"postgres", "n8n"}:
            dirs[:] = [d for d in dirs if d != "data"]
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        rdir = f"{remote}/{posix}" if posix != "." else remote
        mkdir_p(sftp, rdir)
        for name in files:
            if name.endswith((".pyc", ".m4a", ".mp3", ".wav", ".ogg", ".rar")):
                continue
            if name == ".env":
                continue
            lp = root_p / name
            print("upload", (rel_dir / name).as_posix() if posix != "." else name)
            sftp.put(str(lp), f"{rdir}/{name}")


def main() -> None:
    c = connect()
    sftp = c.open_sftp()

    run(
        c,
        "id atlasadmin >/dev/null 2>&1 || useradd -m -s /bin/bash atlasadmin; "
        f"echo 'atlasadmin:{ADMIN_PASS}' | chpasswd; "
        "usermod -aG sudo,docker atlasadmin; "
        "echo 'atlasadmin ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/atlasadmin; "
        "chmod 440 /etc/sudoers.d/atlasadmin",
    )

    upload_tree(sftp, LOCAL_DOCKER, REMOTE)

    env = {}
    with sftp.file(f"{REMOTE}/.env", "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k] = v

    env["AI_API_KEY"] = GEMINI_KEY or env.get("AI_API_KEY", "")
    env["AI_MODEL"] = "gemini-2.0-flash"
    env["AI_API_URL"] = "http://llm:8080/v1/chat/completions"
    env["ATLAS_MANAGER_EMAIL"] = SMTP_USER
    env["ATLAS_SMTP_FROM"] = SMTP_USER
    env["SMTP_HOST"] = "smtp.mail.yahoo.com"
    env["SMTP_PORT"] = "587"
    env["SMTP_USER"] = SMTP_USER
    if SMTP_PASS:
        env["SMTP_PASS"] = SMTP_PASS
    env["CORS_ORIGINS"] = "*"

    body = "".join(f"{k}={v}\n" for k, v in env.items())
    with sftp.file(f"{REMOTE}/.env", "w") as f:
        f.write(body)
    sftp.chmod(f"{REMOTE}/.env", 0o600)

    pg_pass = env.get("POSTGRES_PASSWORD", "")
    cred = [{
        "id": "atlas-postgres-cred",
        "name": "Atlas PostgreSQL",
        "type": "postgres",
        "data": {
            "host": "postgres",
            "database": env.get("POSTGRES_DB", "atlas"),
            "user": env.get("POSTGRES_USER", "atlas"),
            "password": pg_pass,
            "port": 5432,
            "ssl": "disable",
        },
    }]
    with sftp.file(f"{REMOTE}/n8n/credentials/postgres.json", "w") as f:
        f.write(json.dumps(cred))

    note = (
        f"Linux user atlasadmin password: {ADMIN_PASS}\n"
        f"SSH: ssh -p 9011 atlasadmin@{HOST}\n"
        f"Panel: http://{HOST}/  password: {env.get('PANEL_PASSWORD','')}\n"
        f"n8n: http://{HOST}:5678/  user: {env.get('N8N_USER','admin')}  password: {env.get('N8N_PASSWORD','')}\n"
        "Root password was NOT changed.\n"
    )
    with sftp.file("/root/atlas-credentials.txt", "w") as f:
        f.write(note)
    sftp.chmod("/root/atlas-credentials.txt", 0o600)
    print(note)

    run(
        c,
        "chown -R 1000:1000 /opt/atlas/n8n/data && "
        "cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build",
        timeout=600,
    )
    time.sleep(12)
    run(c, "docker ps --format '{{.Names}} {{.Status}}'")

    run(
        c,
        "docker exec -u node atlas-n8n n8n import:credentials --input=/opt/atlas-import/credentials/postgres.json || true; "
        "docker exec -u node atlas-n8n n8n import:workflow --input=/opt/atlas-import/workflows/atlas-call-intelligence-v1.json || true; "
        "docker exec -u node atlas-n8n n8n import:workflow --input=/opt/atlas-import/workflows/atlas-call-intelligence-monthly-report.json || true",
        timeout=120,
    )
    run(
        c,
        """docker exec atlas-postgres psql -U atlas -d atlas -c "UPDATE workflow_entity SET active = true WHERE name ILIKE 'Atlas%'; SELECT id, name, active FROM workflow_entity;" """,
    )
    run(c, "docker restart atlas-n8n atlas-mailer atlas-llm atlas-panel")
    time.sleep(15)
    run(c, "docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'")
    run(c, "docker logs atlas-llm --tail 20 || true")
    run(c, "curl -sS http://127.0.0.1:5678/healthz; echo; curl -sS http://127.0.0.1/login | head -c 200; echo")

    sftp.close()
    c.close()
    print("provision done")


if __name__ == "__main__":
    main()
