#!/usr/bin/env python3
"""Upload the panel source to the VPS and rebuild only the panel container."""
import os
import sys
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_env import load_docker_env

load_docker_env()
if not os.environ.get("ATLAS_VPS_PASSWORD"):
    raise SystemExit("ATLAS_VPS_PASSWORD را در docker/.env یا محیط سیستم تنظیم کنید.")

LOCAL = Path(__file__).resolve().parents[1]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root", password=os.environ["ATLAS_VPS_PASSWORD"],
          timeout=30, allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
files = [p for p in (LOCAL / "panel").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
for p in files:
    rel = str(p.relative_to(LOCAL)).replace("\\", "/")
    sftp.put(str(p), f"/opt/atlas/{rel}")
sftp.close()
print(f"uploaded {len(files)} panel files")
local_env = {}
env_path = LOCAL / ".env"
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            local_env[k.strip()] = v.strip()
ai_key = (local_env.get("AI_API_KEY") or "").strip()
if ai_key:
    esc = ai_key.replace("'", "'\"'\"'")
    c.exec_command(
        f"grep -q '^AI_API_KEY=' /opt/atlas/.env && sed -i 's#^AI_API_KEY=.*#AI_API_KEY={ai_key}#' /opt/atlas/.env "
        f"|| echo 'AI_API_KEY={ai_key}' >> /opt/atlas/.env",
        timeout=60,
    )
_, o, _ = c.exec_command(
    "cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build --force-recreate panel 2>&1 | tail -5"
    " && sleep 6 && docker logs atlas-panel --tail 8 2>&1", timeout=900)
print(o.read().decode(errors="replace"))
c.close()
