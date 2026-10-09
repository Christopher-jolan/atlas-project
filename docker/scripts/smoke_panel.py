#!/usr/bin/env python3
"""Log into the panel on the VPS and hit every page/API; report status codes."""
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)

script = r'''
docker exec atlas-postgres psql -U atlas -d atlas -c "DELETE FROM call_analyses WHERE call_id LIKE 'test-%';"
CALL_ID=$(docker exec atlas-postgres psql -U atlas -d atlas -tAc "SELECT call_id FROM call_analyses WHERE call_id LIKE 'web-%' ORDER BY id DESC LIMIT 1")
PW=$(grep '^PANEL_PASSWORD=' /opt/atlas/.env | cut -d= -f2-)
J=/tmp/atlas_cookies
rm -f $J
curl -sS -o /dev/null -c $J -X POST --data-urlencode "password=$PW" http://127.0.0.1/login
for p in / /upload /search?q=test /top-performers /ready-to-buy /unhappy-customers /staff-performance \
         /call-duration /satisfaction /successful-sales /monthly-reports /ai-insights /settings \
         /calls/$CALL_ID /export/recent /api/stats /api/recent-calls /api/trend /api/departments \
         /api/top-performers /api/health /api/ai-insights; do
  code=$(curl -sS -o /tmp/body -w '%{http_code}' -b $J --max-time 180 "http://127.0.0.1$p")
  echo "$code $p"
  if [ "$code" != "200" ]; then head -c 300 /tmp/body; echo; fi
done
echo "--- ai-insights sample ---"
curl -sS -b $J --max-time 180 http://127.0.0.1/api/ai-insights | head -c 400; echo
echo "--- unauthenticated page should redirect ---"
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1/settings
'''
_, o, e = c.exec_command(script, timeout=900)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print("STDERR:", err[-800:])
c.close()
