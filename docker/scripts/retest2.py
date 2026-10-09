import json, os, sys, time
import paramiko
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
sftp.put(str(Path(__file__).resolve().parents[1] / "llm" / "bridge.py"), "/opt/atlas/llm/bridge.py")


def run(cmd, timeout=180):
    print(">>>", cmd[:150])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    print(out[-2200:] if len(out) > 2200 else out)
    if err:
        print(err[-600:] if len(err) > 600 else err)
    print("exit", o.channel.recv_exit_status())
    return out

run("cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build llm")
time.sleep(5)
run("docker exec atlas-n8n printenv AI_MODEL API_URL")
run(r"""python3 - <<'PY'
import json, urllib.request
payload = {
  "call_id": "test-gemini-003",
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
with urllib.request.urlopen(req, timeout=150) as r:
    data = json.loads(r.read().decode())
qc = (data.get("analysis") or {}).get("quality_control") or {}
cust = (data.get("analysis") or {}).get("customer") or {}
print("success", data.get("success"))
print("email_sent", data.get("email_sent"), "email_error", data.get("email_error"))
print("flags", qc.get("analysis_flags"), "review", qc.get("needs_human_review"))
print("summary", (cust.get("request_summary") or "")[:200])
print("intent", ((data.get("analysis") or {}).get("sales_analysis") or {}).get("purchase_intent_score"))
PY""")
run("docker logs atlas-llm --tail 20")
run("""docker exec atlas-mailer python -c 'import json,urllib.request; req=urllib.request.Request("http://127.0.0.1:8765/send", data=json.dumps({"to":"mohamad.j1380@yahoo.com","subject":"Atlas VPS test","body":"mailer ok"}).encode(), method="POST", headers={"Content-Type":"application/json"}); print(urllib.request.urlopen(req, timeout=45).read().decode())' """)
sftp.close(); c.close()
