import os, sys, time
import paramiko
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LOCAL = Path(__file__).resolve().parents[1]
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
sftp.put(str(LOCAL / "llm/bridge.py"), "/opt/atlas/llm/bridge.py")
sftp.put(str(LOCAL / "panel/app/gemini.py"), "/opt/atlas/panel/app/gemini.py")


def run(cmd, timeout=360):
    print(">>>", cmd[:140])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print(out[-2500:] if len(out) > 2500 else out)
    if err:
        print(err[-500:] if len(err) > 500 else err)
    print("exit", o.channel.recv_exit_status())
    return out

run("cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build llm panel")
time.sleep(6)
run("docker exec atlas-postgres psql -U atlas -d atlas -c \"UPDATE workflow_entity SET active=true WHERE name ILIKE 'Atlas%';\"")
run("timeout 8 bash -c 'echo > /dev/tcp/smtp.mail.yahoo.com/587' && echo SMTP587_OPEN || echo SMTP587_BLOCKED")
run("timeout 8 bash -c 'echo > /dev/tcp/smtp.mail.yahoo.com/465' && echo SMTP465_OPEN || echo SMTP465_BLOCKED")
run(r"""python3 - <<'PY'
import json, urllib.request
payload = {
  "call_id": "test-gemini-004",
  "transcript": "اپراتور: سلام وقت بخیر شرکت اطلس. مشتری: سلام قیمت نرم افزار حسابداری چقدره؟ میخوام برای شرکت بخرم ولی گرونه. اپراتور: با دوازده درصد تخفیف فاکتور میکنم. مشتری: اوکی بفرستید پیگیری میکنم.",
  "agent_name": "علی رضایی",
  "customer_name": "شرکت آلفا",
  "department": "sales"
}
req = urllib.request.Request(
  "http://127.0.0.1:5678/webhook/atlas/call-intelligence",
  data=json.dumps(payload).encode(),
  method="POST",
  headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=240) as r:
    data = json.loads(r.read().decode())
qc = (data.get("analysis") or {}).get("quality_control") or {}
print("success", data.get("success"), "email", data.get("email_sent"))
print("flags", qc.get("analysis_flags"))
print("intent", ((data.get("analysis") or {}).get("sales_analysis") or {}).get("purchase_intent_score"))
print("summary", (((data.get("analysis") or {}).get("customer") or {}).get("request_summary") or "")[:180])
PY""")
run("docker logs atlas-llm --tail 25")
sftp.close(); c.close()
