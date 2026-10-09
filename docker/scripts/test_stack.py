#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(
    "141.11.21.147",
    port=9011,
    username="root",
    password=os.environ["ATLAS_VPS_PASSWORD"],
    timeout=30,
    allow_agent=False,
    look_for_keys=False,
)


def run(cmd, timeout=180):
    print(">>>", cmd[:160])
    _, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    print(out[-2500:] if len(out) > 2500 else out)
    if err:
        print(err[-1200:] if len(err) > 1200 else err)
    print("exit", code)
    return code, out


run("docker restart atlas-caddy")
run(
    """python3 - <<'PY'
import json, os, urllib.request, urllib.error
# load key from compose env via docker
import subprocess
key = subprocess.check_output("docker exec atlas-llm printenv AI_API_KEY", shell=True, text=True).strip()
print("key_len", len(key), "prefix", key[:6])
for model in ["gemini-2.0-flash","gemini-1.5-flash","gemini-pro"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = json.dumps({"contents":[{"parts":[{"text":"بگو فقط: ok"}]}]}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read().decode())
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
        print("GEMINI_OK", model, txt[:80])
        break
    except urllib.error.HTTPError as e:
        print("GEMINI_FAIL", model, e.code, e.read()[:300])
    except Exception as e:
        print("GEMINI_ERR", model, type(e).__name__, e)
PY"""
)

run(
    """docker exec atlas-llm python - <<'PY'
import json, urllib.request
req = urllib.request.Request(
    "http://127.0.0.1:8080/v1/chat/completions",
    data=json.dumps({"model":"gemini-2.0-flash","messages":[{"role":"user","content":"Return JSON {\\"ok\\": true} only"}]}).encode(),
    method="POST",
    headers={"Content-Type":"application/json"},
)
with urllib.request.urlopen(req, timeout=60) as r:
    print(r.read()[:500])
PY"""
)

run(
    r"""curl -sS -m 20 -X POST http://127.0.0.1:5678/webhook/atlas/call-intelligence -H 'Content-Type: application/json' -d '{"call_id":"test-vps-001","transcript":"اپراتور: سلام وقت بخیر. مشتری: سلام، قیمت نرم افزار حسابداری تون چقدره؟ میخوام بخرم ولی گرونه. اپراتور: با ده درصد تخفیف میتونیم فاکتور کنیم. مشتری: باشه بفرستید.","agent_name":"علی","customer_name":"شرکت تست","department":"sales"}' """
, 180)

run("docker logs atlas-llm --tail 30")
run("docker logs atlas-mailer --tail 20")
run("docker logs atlas-n8n --tail 40")
run("docker exec atlas-postgres psql -U atlas -d atlas -c 'SELECT call_id, department, purchase_intent_score, satisfaction_final_score FROM call_analyses ORDER BY id DESC LIMIT 5;'")
c.close()
