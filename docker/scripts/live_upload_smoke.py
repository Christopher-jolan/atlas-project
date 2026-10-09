#!/usr/bin/env python3
import json
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
cmd = r"""
if [ ! -f /opt/atlas/tmp/test.m4a ]; then echo NO_AUDIO; exit 0; fi
curl -sS -m 900 -X POST https://atlas.mmdjolan.ir/api/upload-voice \
  -F 'file=@/opt/atlas/tmp/test.m4a;type=audio/mp4' \
  -F 'agent_name=تست ارائه' -F 'customer_name=مشتری' -F 'department=auto' \
  -o /opt/atlas/tmp/smoke-upload.json -w 'HTTP %{http_code}\n'
python3 - <<'PY'
import json
p='/opt/atlas/tmp/smoke-upload.json'
d=json.load(open(p,encoding='utf-8'))
if 'detail' in d:
    print('ERROR', d['detail'])
else:
    raw=json.dumps(d, ensure_ascii=False)
    print('success', d.get('success'), 'dept', d.get('department'))
    print('summary', (d.get('summary') or '')[:200])
    print('fallback_tag', 'fallback' in raw.lower())
    print('scores', d.get('scores'))
PY
docker logs atlas-panel --tail 15 2>&1
"""
_, o, e = c.exec_command(cmd, timeout=1000)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print("STDERR", err)
c.close()
