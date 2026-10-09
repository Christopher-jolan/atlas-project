#!/usr/bin/env python3
"""Upload an audio file to the VPS and probe Gemini transcription per model."""
import os
import sys

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUDIO = sys.argv[1]
REMOTE_AUDIO = "/opt/atlas/tmp/test.m4a"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
try:
    sftp.mkdir("/opt/atlas/tmp")
except IOError:
    pass
sftp.put(AUDIO, REMOTE_AUDIO)
sftp.close()

probe = r'''
docker cp /opt/atlas/tmp/test.m4a atlas-panel:/tmp/test.m4a
docker exec -i atlas-panel python - <<'PY'
import base64, json, os, httpx
key = os.environ["AI_API_KEY"]
data = base64.b64encode(open("/tmp/test.m4a","rb").read()).decode()
prompt = "این یک تماس تلفنی فارسی است. کل مکالمه را کلمه به کلمه رونویسی کن. هر جمله را با «اپراتور:» یا «مشتری:» مشخص کن."
for model in ["gemini-3.5-transcribe", "gemini-2.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {"contents":[{"parts":[{"inline_data":{"mime_type":"audio/mp4","data":data}},{"text":prompt}]}],
            "generationConfig":{"temperature":0.1}}
    try:
        r = httpx.post(url, json=body, timeout=600)
        j = r.json()
        if r.status_code >= 400:
            print(model, "HTTP", r.status_code, json.dumps(j)[:300]); continue
        cand = (j.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "\n".join(p.get("text","") for p in parts)
        print(model, "finish", cand.get("finishReason"), "len", len(text), "usage", j.get("usageMetadata",{}).get("candidatesTokenCount"))
        print("  sample:", text[:300].replace("\n"," | "))
        if not text:
            print("  raw:", json.dumps(j, ensure_ascii=False)[:600])
    except Exception as e:
        print(model, "ERR", type(e).__name__, e)
PY
'''
_, o, e = c.exec_command(probe, timeout=1800)
print(o.read().decode(errors="replace"))
err = e.read().decode(errors="replace")
if err:
    print("STDERR:", err[-1500:])
c.close()
