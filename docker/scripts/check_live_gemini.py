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
cmd = r"""docker exec atlas-panel python -c "
from app.ai_keys import gemini_api_key
k=gemini_api_key()
print('gemini_key_len', len(k))
"
curl -sS https://atlas.mmdjolan.ir/api/health
"""
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
