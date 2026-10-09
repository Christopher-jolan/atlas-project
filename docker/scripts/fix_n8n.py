import os
import sys
import time

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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


def run(cmd: str) -> None:
    print(">>>", cmd)
    _, stdout, stderr = c.exec_command(cmd, timeout=120)
    print(stdout.read().decode(errors="replace"))
    err = stderr.read().decode(errors="replace")
    if err:
        print(err)
    print("exit", stdout.channel.recv_exit_status())


run("chown -R 1000:1000 /opt/atlas/n8n/data && docker restart atlas-n8n")
time.sleep(10)
run("docker ps -a --format '{{.Names}} {{.Status}} {{.Ports}}'")
run("docker logs atlas-n8n --tail 50")
c.close()
