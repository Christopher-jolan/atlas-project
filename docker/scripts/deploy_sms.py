#!/usr/bin/env python3
"""Deploy the SMS (Ghasedak) feature: panel, compose, workflow and SMS env values."""
import os
import sys
import time
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/opt/atlas"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root", password=os.environ["ATLAS_VPS_PASSWORD"],
          timeout=30, allow_agent=False, look_for_keys=False)


def run(cmd, timeout=600):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = (o.read() + e.read()).decode(errors="replace").strip()
    if out:
        print(out)
    return out


sftp = c.open_sftp()
files = [p for p in (LOCAL / "panel").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
files += [LOCAL / "docker-compose.prod.yml", LOCAL / "n8n/workflows/atlas-call-intelligence-v1.json"]
for p in files:
    sftp.put(str(p), f"{REMOTE}/{str(p.relative_to(LOCAL)).replace(chr(92), '/')}")
sftp.close()
print(f"uploaded {len(files)} files")

env_values = {
    "GHASEDAK_API_KEY": os.environ.get("GHASEDAK_API_KEY", ""),
    "SMS_LINE_NUMBER": "2170003727",
    "SMS_MANAGER_NUMBERS": "09198010013",
}
for k, v in env_values.items():
    if v:
        run(f"grep -q '^{k}=' {REMOTE}/.env && sed -i 's#^{k}=.*#{k}={v}#' {REMOTE}/.env || echo '{k}={v}' >> {REMOTE}/.env")

run(f"cd {REMOTE} && docker compose -f docker-compose.prod.yml --env-file .env up -d --build panel 2>&1 | tail -3", 900)
time.sleep(6)
run("docker logs atlas-panel --tail 5 2>&1")
run("docker exec atlas-postgres psql -U atlas -d atlas -tAc "
    "\"SELECT key, CASE WHEN key='sms_api_key' THEN left(value,4)||'…' ELSE value END FROM panel_settings WHERE key LIKE 'sms_%' ORDER BY key\"")
run("docker exec -u node atlas-n8n n8n import:workflow --input=/opt/atlas-import/workflows/atlas-call-intelligence-v1.json 2>&1 | tail -1")
run("docker exec atlas-postgres psql -U atlas -d atlas -tAc \"UPDATE workflow_entity SET active = true WHERE name ILIKE 'Atlas%' RETURNING name\"")
run("docker restart atlas-n8n >/dev/null && sleep 15 && docker logs atlas-n8n --tail 3 2>&1")
c.close()
