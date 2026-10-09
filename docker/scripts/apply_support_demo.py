#!/usr/bin/env python3
import os
from pathlib import Path

import paramiko

LOCAL = Path(__file__).resolve().parents[1] / "postgres/init/004_support_demo_calls.sql"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    os.environ.get("ATLAS_VPS_HOST", "141.11.21.147"),
    port=9011,
    username="root",
    password=os.environ["ATLAS_VPS_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)
sftp = c.open_sftp()
sftp.put(str(LOCAL), "/opt/atlas/postgres/init/004_support_demo_calls.sql")
sftp.close()
_, o, e = c.exec_command(
    "docker exec -i atlas-postgres psql -U atlas -d atlas -f /docker-entrypoint-initdb.d/004_support_demo_calls.sql"
)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
_, o2, _ = c.exec_command(
    "docker exec atlas-postgres psql -U atlas -d atlas -c "
    "\"SELECT department, COUNT(*)::int AS n FROM call_analyses GROUP BY department ORDER BY department;\""
)
print(o2.read().decode(errors="replace"))
c.close()
