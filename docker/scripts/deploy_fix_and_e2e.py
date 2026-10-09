#!/usr/bin/env python3
"""Push transcription/analysis fixes, re-import the n8n workflow, run an end-to-end upload test."""
import os
import sys
import time
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LOCAL = Path(__file__).resolve().parents[1]
AUDIO = sys.argv[1] if len(sys.argv) > 1 else None

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
for rel in [
    "llm/bridge.py",
    "panel/app/gemini.py",
    "panel/app/transcribe.py",
    "panel/app/ai.py",
    "docker-compose.prod.yml",
    "n8n/workflows/atlas-call-intelligence-v1.json",
]:
    sftp.put(str(LOCAL / rel), f"/opt/atlas/{rel}")
    print("put", rel)
if AUDIO:
    sftp.put(AUDIO, "/opt/atlas/tmp/test.m4a")
    print("put audio")
sftp.close()


def run(cmd, timeout=900):
    print("\n>>>", cmd.strip().splitlines()[0][:150])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    print(out[-3000:] if len(out) > 3000 else out)
    if err and code != 0:
        print("STDERR:", err[-1200:])
    print("exit", code)
    return out


run("grep -q '^RATE_LIMIT_RPM=' /opt/atlas/.env || echo 'RATE_LIMIT_RPM=6' >> /opt/atlas/.env")
run("cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build llm panel 2>&1 | tail -5")
run("docker exec -u node atlas-n8n n8n import:workflow --input=/opt/atlas-import/workflows/atlas-call-intelligence-v1.json 2>&1 | tail -3")
run("""docker exec atlas-postgres psql -U atlas -d atlas -c "UPDATE workflow_entity SET active = true WHERE name ILIKE 'Atlas%';" """)
run("docker restart atlas-n8n")
time.sleep(20)
run("docker logs atlas-n8n --tail 12 2>&1")

if AUDIO:
    run(r"""
curl -sS -m 900 -X POST http://127.0.0.1/api/upload-voice \
  -F "file=@/opt/atlas/tmp/test.m4a;type=audio/mp4" \
  -F "agent_name=اپراتور آتیران" -F "customer_name=مشتری فروشگاه" -F "department=auto" \
  -o /opt/atlas/tmp/e2e.json -w 'HTTP %{http_code} in %{time_total}s\n'
python3 - <<'PY'
import json
d = json.load(open("/opt/atlas/tmp/e2e.json", encoding="utf-8"))
if "detail" in d:
    print("ERROR:", d["detail"])
else:
    print("success:", d.get("success"), "| call_id:", d.get("call_id"), "| dept:", d.get("department"))
    print("email_sent:", d.get("email_sent"), "| transcript chars:", d.get("transcript_length"))
    print("scores:", d.get("scores"))
    print("summary:", (d.get("summary") or "")[:400])
PY
""", timeout=1000)
    run("docker logs atlas-llm --tail 8 2>&1")
    run("docker logs atlas-panel --tail 6 2>&1")
    run("""docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT call_id, department, purchase_intent_score AS intent, satisfaction_final_score AS sat, agent_quality_score AS agent, needs_human_review AS review, length(transcript_text) AS chars FROM call_analyses ORDER BY id DESC LIMIT 3;" """)

c.close()
