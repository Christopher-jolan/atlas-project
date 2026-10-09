#!/usr/bin/env python3
import os
import sys
from pathlib import Path

import paramiko

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_env import load_docker_env

load_docker_env()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "141.11.21.147", port=9011, username="root",
    password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
    allow_agent=False, look_for_keys=False,
)
cmd = r"""docker exec atlas-panel python - <<'PY'
import json, os, urllib.request, urllib.error
key=os.environ['AI_API_KEY']
for model in ['gemini-2.5-flash','gemini-flash-latest','gemini-2.0-flash','gemini-3.5-flash-lite']:
    url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}'
    body=json.dumps({'contents':[{'parts':[{'text':'say ok'}]}]}).encode()
    req=urllib.request.Request(url,data=body,method='POST',headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            print(model,'OK',r.read()[:80])
    except urllib.error.HTTPError as e:
        print(model,'HTTP',e.code,e.read()[:180])
PY"""
_, o, _ = c.exec_command(cmd, timeout=120)
print(o.read().decode(errors="replace"))
c.close()
