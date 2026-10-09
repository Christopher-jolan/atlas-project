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
files = [
    ("llm/bridge.py", "/opt/atlas/llm/bridge.py"),
    ("panel/app/gemini.py", "/opt/atlas/panel/app/gemini.py"),
    ("panel/app/transcribe.py", "/opt/atlas/panel/app/transcribe.py"),
    ("docker-compose.prod.yml", "/opt/atlas/docker-compose.prod.yml"),
]
for rel, rem in files:
    sftp.put(str(LOCAL / rel.replace("docker-compose.prod.yml", "docker-compose.prod.yml") if False else LOCAL / Path(rel)), rem)
    print("put", rel)


def run(cmd, timeout=300):
    print(">>>", cmd[:160])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out, err = o.read().decode(errors="replace"), e.read().decode(errors="replace")
    print(out[-2000:] if len(out) > 2000 else out)
    if err:
        print(err[-800:] if len(err) > 800 else err)
    print("exit", o.channel.recv_exit_status())
    return out

run("sed -i 's/AI_MODEL=.*/AI_MODEL=gemini-2.5-flash/' /opt/atlas/.env")
run("cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d --build llm panel", 300)
time.sleep(8)
run("""python3 - <<'PY'
import json, subprocess, urllib.request
body = json.dumps({
  "model":"gemini-2.5-flash",
  "messages":[{"role":"user","content":"Return ONLY JSON: {\\"meta\\":{\\"department\\":\\"sales\\"},\\"customer\\":{\\"request_summary\\":\\"قیمت\\",\\"satisfaction\\":{\\"final_score\\":70}},\\"sales_analysis\\":{\\"purchase_intent_score\\":80,\\"applicable\\":true},\\"agent_performance\\":{\\"response_quality_score\\":75},\\"ticket\\":{\\"title\\":\\"پیگیری\\",\\"priority\\":\\"high\\"},\\"quality_control\\":{\\"needs_human_review\\":false}}"}]
}).encode()
req = urllib.request.Request("http://127.0.0.1:5678/webhook/atlas/call-intelligence", data=json.dumps({
  "call_id":"test-gemini-002",
  "transcript":"اپراتور: سلام. مشتری: قیمت نرم افزار حسابداری چقدره میخوام بخرم. اپراتور: با ده درصد تخفیف فاکتور میکنیم. مشتری: اوکی بفرستید.",
  "agent_name":"علی","customer_name":"شرکت تست","department":"sales"
}).encode(), method="POST", headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=120) as r:
    data = json.loads(r.read().decode())
print("success", data.get("success"), "email", data.get("email_sent"), "dept", data.get("department"))
flags = (data.get("analysis") or {}).get("quality_control", {})
print("flags", flags)
print("summary", ((data.get("analysis") or {}).get("customer") or {}).get("request_summary","")[:120])
PY""")
run("""python3 - <<'PY'
import json, subprocess
# mailer test from inside docker network
print(subprocess.check_output(
  "docker exec atlas-mailer python -c \"import json,urllib.request; req=urllib.request.Request('http://127.0.0.1:8765/send', data=json.dumps({'to':'mohamad.j1380@yahoo.com','subject':'Atlas test','body':'test from VPS'}).encode(), method='POST', headers={'Content-Type':'application/json'}); print(urllib.request.urlopen(req, timeout=40).read().decode())\"",
  shell=True, text=True, stderr=subprocess.STDOUT))
PY""")
run("docker logs atlas-llm --tail 15")
run("docker exec atlas-postgres psql -U atlas -d atlas -c \"SELECT call_id, department, purchase_intent_score FROM call_analyses WHERE call_id LIKE 'test%' ORDER BY id DESC;\"")
sftp.close(); c.close()
