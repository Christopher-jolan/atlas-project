#!/usr/bin/env python3
"""Upload the panel source to the VPS and rebuild only the panel container."""
import os
import sys
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
_, o, _ = c.exec_command(
    "cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build panel 2>&1 | tail -3"
    " && sleep 4 && docker logs atlas-panel --tail 5 2>&1", timeout=900)
print(o.read().decode(errors="replace"))
c.close()
