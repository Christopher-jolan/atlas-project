import os
import sys
import json
import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "141.11.21.147", port=9011, username="root",
    password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
    allow_agent=False, look_for_keys=False,
)
cmd = r'''python3 - <<'PY'
import json, subprocess, urllib.request
key = subprocess.check_output("docker exec atlas-llm printenv AI_API_KEY", shell=True, text=True).strip()
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
with urllib.request.urlopen(url, timeout=40) as r:
    data = json.loads(r.read().decode())
names = []
for m in data.get("models", []):
    name = m.get("name","")
    methods = m.get("supportedGenerationMethods") or []
    if "generateContent" in methods:
        names.append(name.replace("models/",""))
print("COUNT", len(names))
for n in names:
    print(n)
PY'''
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
