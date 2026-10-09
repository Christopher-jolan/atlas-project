import os, sys, paramiko
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("141.11.21.147", port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30,
          allow_agent=False, look_for_keys=False)
app_pass = os.environ["ATLAS_SMTP_APP_PASS"]

def run(cmd, timeout=90):
    print(">>>", cmd[:100])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    print(o.read().decode(errors="replace")[-1500:])
    err = e.read().decode(errors="replace")
    if err:
        print(err[-400:])
    print("exit", o.channel.recv_exit_status())

# escape for sed: use python to rewrite env line
sftp = c.open_sftp()
env = sftp.file("/opt/atlas/.env").read().decode()
lines = []
for line in env.splitlines():
    if line.startswith("SMTP_PASS="):
        lines.append("SMTP_PASS=" + app_pass)
    else:
        lines.append(line)
sftp.file("/opt/atlas/.env", "w").write("\n".join(lines) + "\n")
sftp.close()
run("cd /opt/atlas && docker compose -f docker-compose.prod.yml --env-file .env up -d mailer")
run("""docker exec atlas-mailer python -c 'import json,urllib.request; req=urllib.request.Request("http://127.0.0.1:8765/send", data=json.dumps({"to":"mohamad.j1380@yahoo.com","subject":"Atlas VPS test","body":"mailer ok"}).encode(), method="POST", headers={"Content-Type":"application/json"}); print(urllib.request.urlopen(req, timeout=45).read().decode())' """)
c.close()
