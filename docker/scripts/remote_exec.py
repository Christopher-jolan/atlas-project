#!/usr/bin/env python3
"""Run a shell command on the Atlas VPS: python remote_exec.py "<cmd>" """
import os
import sys
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_env import load_docker_env

load_docker_env()

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    os.environ.get("ATLAS_VPS_HOST", "141.11.21.147"),
    port=int(os.environ.get("ATLAS_VPS_PORT", "9011")),
    username=os.environ.get("ATLAS_VPS_USER", "root"),
    password=os.environ["ATLAS_VPS_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
_, stdout, stderr = c.exec_command(sys.argv[1], timeout=int(os.environ.get("ATLAS_TIMEOUT", "600")))
print(stdout.read().decode(errors="replace"))
err = stderr.read().decode(errors="replace")
if err:
    print("STDERR:", err)
print("exit", stdout.channel.recv_exit_status())
c.close()
