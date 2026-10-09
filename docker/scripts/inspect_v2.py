"""Inspect panel settings, users and the last e2e notification result on the VPS."""
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root", password=os.environ["ATLAS_VPS_PASSWORD"],
          timeout=30, allow_agent=False, look_for_keys=False)
arg = sys.argv[1] if len(sys.argv) > 1 else ""
if arg and os.path.isfile(arg):
    arg = open(arg, encoding="utf-8").read()
cmd = arg or r"""
grep -o '"email_[a-z]*": [^,]*' /opt/atlas/tmp/e2e.json
docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT key, left(value, 60) AS value FROM panel_settings ORDER BY key;"
docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT id, username, role, is_active FROM users;"
docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT call_id, customer_name, agent_name, analyzed_at FROM call_analyses ORDER BY id DESC LIMIT 8;"
"""
_, o, e = c.exec_command(cmd, timeout=600)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace")[-2000:])
c.close()
