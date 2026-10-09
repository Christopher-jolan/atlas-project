#!/usr/bin/env python3
"""Deploy panel v2 (users, white-label, responsive UI, Persian email) + HTTPS, then smoke + e2e test.

Usage: ATLAS_VPS_PASSWORD=... python deploy_v2.py [--no-e2e]
"""
import os
import sys
import time
from pathlib import Path

import paramiko

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LOCAL = Path(__file__).resolve().parents[1]
REMOTE = "/opt/atlas"


def _read_local_dotenv() -> dict[str, str]:
    path = LOCAL / ".env"
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out
DOMAIN = os.environ.get("ATLAS_DOMAIN", "atlas.mmdjolan.ir")
RUN_E2E = "--no-e2e" not in sys.argv

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ.get("ATLAS_VPS_HOST", "141.11.21.147"), port=9011, username="root",
          password=os.environ["ATLAS_VPS_PASSWORD"], timeout=30, allow_agent=False, look_for_keys=False)


def run(cmd, timeout=900, quiet=False):
    if not quiet:
        print("\n>>>", cmd.strip().splitlines()[0][:160])
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode(errors="replace")
    err = e.read().decode(errors="replace")
    code = o.channel.recv_exit_status()
    if not quiet:
        print(out[-4000:])
        if err and code != 0:
            print("STDERR:", err[-1500:])
        print("exit", code)
    return out


sftp = c.open_sftp()
files = [p for p in (LOCAL / "panel").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
files += [LOCAL / "mailer/mailer.py", LOCAL / "Caddyfile", LOCAL / "docker-compose.prod.yml",
          LOCAL / "n8n/workflows/atlas-call-intelligence-v1.json",
          LOCAL / "postgres/init/004_support_demo_calls.sql"]
dirs = sorted({str(p.parent.relative_to(LOCAL)).replace("\\", "/") for p in files})
run("mkdir -p " + " ".join(f"{REMOTE}/{d}" for d in dirs) + f" {REMOTE}/caddy/data {REMOTE}/caddy/config", quiet=True)
for p in files:
    rel = str(p.relative_to(LOCAL)).replace("\\", "/")
    sftp.put(str(p), f"{REMOTE}/{rel}")
print(f"uploaded {len(files)} files")
sftp.close()

env_values = {
    "PANEL_DOMAIN": DOMAIN,
    "PANEL_PUBLIC_URL": f"https://{DOMAIN}",
    "PUBLIC_DEMO_API": "true",
    "CORS_ORIGINS": "https://mmdjolan.ir,https://www.mmdjolan.ir,http://mmdjolan.ir,http://www.mmdjolan.ir",
    "UPLOAD_MAX_MB": "50",
}
for k, v in env_values.items():
    run(f"grep -q '^{k}=' {REMOTE}/.env && sed -i 's#^{k}=.*#{k}={v}#' {REMOTE}/.env || echo '{k}={v}' >> {REMOTE}/.env", quiet=True)

local_env = _read_local_dotenv()
ai_key = (local_env.get("AI_API_KEY") or "").strip()
if ai_key:
    run(
        f"grep -q '^AI_API_KEY=' {REMOTE}/.env && "
        f"sed -i 's#^AI_API_KEY=.*#AI_API_KEY={ai_key}#' {REMOTE}/.env || "
        f"echo 'AI_API_KEY={ai_key}' >> {REMOTE}/.env",
        quiet=True,
    )
    print("synced AI_API_KEY from local docker/.env to VPS")

run(f"grep -E '^(PANEL_DOMAIN|PANEL_PUBLIC_URL|PUBLIC_DEMO_API|CORS_ORIGINS|UPLOAD_MAX_MB|AI_API_KEY)=' {REMOTE}/.env | sed 's/AI_API_KEY=.*/AI_API_KEY=***redacted***/'")

run("ufw status | head -3; (ufw status | grep -q 'Status: active' && ufw allow 443/tcp && ufw allow 443/udp) || true")
run(f"cd {REMOTE} && docker compose -f docker-compose.prod.yml --env-file .env up -d --build panel llm mailer caddy n8n 2>&1 | tail -12", timeout=1200)
time.sleep(15)
run("docker exec -u node atlas-n8n n8n import:workflow --input=/opt/atlas-import/workflows/atlas-call-intelligence-v1.json 2>&1 | tail -2")
run("""docker exec atlas-postgres psql -U atlas -d atlas -c "UPDATE workflow_entity SET active = true WHERE name ILIKE 'Atlas%' RETURNING name, active;" """)
run("docker restart atlas-n8n && sleep 20 && docker logs atlas-n8n --tail 6 2>&1")
run("docker logs atlas-panel --tail 15 2>&1")
run("docker exec -i atlas-postgres psql -U atlas -d atlas -f /docker-entrypoint-initdb.d/004_support_demo_calls.sql")
run(r"""docker exec -i atlas-postgres psql -U atlas -d atlas <<'SQL'
UPDATE panel_settings SET value = (SELECT COALESCE(NULLIF(value, ''), 'mohamad.j1380@yahoo.com') FROM panel_settings WHERE key = 'manager_email')
  WHERE key = 'notify_emails' AND value = '';
UPDATE panel_settings SET value = 'نرم‌افزار حسابداری و مدیریت فروش برای فروشگاه‌ها، عمده‌فروشان و شرکت‌های پخش؛ شامل ماژول‌های فروش مویرگی، انبارداری، ردیابی ویزیتور با GPS، گزارش‌های مالی و خدمات پشتیبانی و آموزش. روند فروش معمول: معرفی قابلیت‌ها، ارسال پیش‌فاکتور، پیگیری تلفنی، نصب و آموزش.'
  WHERE key = 'business_context' AND value = '';
DELETE FROM call_analyses WHERE call_id IN ('web-ddd673b1289d', 'web-dc3b835bdcd6', 'web-8cc0d819f492', 'web-acbf31c6d3ba');
SELECT key, left(value, 50) FROM panel_settings WHERE key IN ('notify_emails', 'business_context');
SQL""")
run("docker logs atlas-caddy --tail 25 2>&1 | grep -Ei 'certificate|error|obtain|serving' | tail -12")

print("\n===== HTTPS checks =====")
run(f"curl -sS -o /dev/null -w 'https login: %{{http_code}} ssl_verify=%{{ssl_verify_result}}\\n' https://{DOMAIN}/login")
run(f"curl -sS -o /dev/null -w 'http domain: %{{http_code}} -> %{{redirect_url}}\\n' http://{DOMAIN}/login")
run("curl -sS -o /dev/null -w 'http ip: %{http_code}\\n' http://127.0.0.1/login")
run(f"curl -sS -I -H 'Origin: https://mmdjolan.ir' https://{DOMAIN}/api/stats | grep -i -E 'HTTP/|access-control'")

print("\n===== Smoke test (logged in as admin) =====")
smoke = r"""
PANEL_PASSWORD=$(grep '^PANEL_PASSWORD=' /opt/atlas/.env | cut -d= -f2-)
B=https://__DOMAIN__
J=/tmp/atlas_cookies.txt; rm -f $J
code=$(curl -sS -c $J -o /dev/null -w '%{http_code}' -X POST $B/login --data-urlencode "username=admin" --data-urlencode "password=$PANEL_PASSWORD" -d remember=on -d next=/)
echo "login POST -> $code"; grep -c atlas_session $J >/dev/null && echo "session cookie set"
for p in / /upload /search "/search?q=a" /ready-to-buy /unhappy-customers /successful-sales /top-performers /staff-performance /satisfaction /call-duration /monthly-reports /ai-insights /settings /users /account /api/stats /api/health /export/recent /calls/does-not-exist /static/css/style.css /static/fonts/Vazirmatn-Variable.woff2; do
  printf '%-28s %s\n' "$p" "$(curl -sS -b $J -o /dev/null -w '%{http_code} %{size_download}B' "$B$p")"
done
first=$(docker exec atlas-postgres psql -U atlas -d atlas -tAc "SELECT call_id FROM call_analyses ORDER BY id DESC LIMIT 1")
[ -n "$first" ] && printf '%-28s %s\n' "/calls/$first" "$(curl -sS -b $J -o /dev/null -w '%{http_code} %{size_download}B' "$B/calls/$first")"
first_m=$(docker exec atlas-postgres psql -U atlas -d atlas -tAc "SELECT id FROM monthly_reports ORDER BY id DESC LIMIT 1")
[ -n "$first_m" ] && printf '%-28s %s\n' "/monthly-reports/$first_m" "$(curl -sS -b $J -o /dev/null -w '%{http_code} %{size_download}B' "$B/monthly-reports/$first_m")"
echo "--- unauthenticated ---"
printf '%-28s %s\n' "/ (no cookie)" "$(curl -sS -o /dev/null -w '%{http_code} -> %{redirect_url}' $B/)"
printf '%-28s %s\n' "/api/upload-voice GET" "$(curl -sS -o /dev/null -w '%{http_code}' $B/api/upload-voice)"
printf '%-28s %s\n' "/api/stats (demo)" "$(curl -sS -o /dev/null -w '%{http_code}' $B/api/stats)"
printf '%-28s %s\n' "bad login" "$(curl -sS -o /dev/null -w '%{http_code} -> %{redirect_url}' -X POST $B/login -d username=admin -d password=wrong)"
echo "--- json in pages? ---"
for p in / /search?q=a; do curl -sS -b $J "$B$p" | grep -c '"analysis_json"\|json-view\|<pre' || true; done
""".replace("__DOMAIN__", DOMAIN)
run(smoke)

if RUN_E2E:
    print("\n===== End-to-end upload (real Atiran call) =====")
    run(r"""
API_TOKEN=$(grep '^API_TOKEN=' /opt/atlas/.env | cut -d= -f2-)
curl -sS -m 900 -X POST https://__DOMAIN__/api/upload-voice -H "X-API-Token: $API_TOKEN" \
  -F "file=@/opt/atlas/tmp/test.m4a;type=audio/mp4" \
  -F "agent_name=کارشناس فروش" -F "customer_name=مشتری آتیران" -F "department=auto" \
  -o /opt/atlas/tmp/e2e.json -w 'HTTP %{http_code} in %{time_total}s\n'
python3 - <<'PY'
import json
d = json.load(open("/opt/atlas/tmp/e2e.json", encoding="utf-8"))
if "detail" in d:
    print("ERROR:", d["detail"])
else:
    for k in ("success", "call_id", "department_label", "priority_label", "email_sent", "transcript_length", "scores", "panel_url"):
        print(f"{k}: {d.get(k)}")
    print("summary:", d.get("summary"))
    print("actions:")
    for a in d.get("actions") or []:
        print("  -", a)
PY
""".replace("__DOMAIN__", DOMAIN), timeout=1000)
    run("docker logs atlas-panel --tail 8 2>&1; docker logs atlas-mailer --tail 4 2>&1")
    run("""docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT call_id, department, call_date, purchase_intent_score AS intent, satisfaction_final_score AS sat, agent_quality_score AS agent, ticket_priority, needs_human_review AS review FROM call_analyses ORDER BY id DESC LIMIT 2;" """)

c.close()
