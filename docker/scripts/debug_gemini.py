import os, sys, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
cmd = r'''docker exec atlas-llm python -c "
import json, os, urllib.request, urllib.error
key=os.environ['AI_API_KEY']
print('model_env', os.environ.get('AI_MODEL'))
print('key_len', len(key))
url=f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}'
body=json.dumps({'contents':[{'parts':[{'text':'say ok'}]}]}).encode()
req=urllib.request.Request(url, data=body, method='POST', headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=40) as r:
        print('OK', r.read()[:400])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read()[:500])
" '''
_, o, e = c.exec_command(cmd, timeout=60)
print(o.read().decode(errors="replace"))
print(e.read().decode(errors="replace"))
c.close()
