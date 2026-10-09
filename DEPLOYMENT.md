# Atlas Project — راهنمای راه‌اندازی کامل

## معماری سیستم

پروژه Atlas یک سیستم هوش تجاری مرکز تماس است با اجزای زیر:

### سرویس‌های Docker

1. **PostgreSQL** (port 15432) — ذخیره تحلیل تماس‌ها
2. **n8n** (port 5678) — اتوماسیون workflow
3. **Panel FastAPI** (port 8080) — داشبورد مدیریتی
4. **Mailer** (port 8765) — ارسال ایمیل

### صفحات وب

مسیر: `mmdjolan.ir/public_html/atlas_project/`

- `upload.html` — آپلود فایل صوتی
- `dashboard.html` — نمایش آمار زنده
- `workflows.html` — مدیریت n8n
- `architecture.html` — معماری سیستم

---

## راه‌اندازی Docker

### 1. بررسی وضعیت فعلی

```bash
cd "F:/atlas project/docker"
docker compose ps
```

**وضعیت فعلی:**
- ✅ postgres, n8n, mailer در حال اجرا
- ❌ panel نیاز به build و start دارد

### 2. ساخت و اجرای Panel

```bash
cd "F:/atlas project/docker"
docker compose build panel
docker compose up -d panel
```

### 3. بررسی لاگ‌ها

```bash
docker logs atlas-panel --tail 50 -f
docker logs atlas-n8n --tail 30
```

### 4. تست سرویس‌ها

```bash
# Test Panel API
curl http://localhost:8080/api/stats

# Test n8n
curl http://localhost:5678/healthz

# Test PostgreSQL
docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT COUNT(*) FROM call_analyses;"
```

---

## تنظیمات محیط (.env)

فایل: `F:/atlas project/docker/.env`

```env
# Database
POSTGRES_USER=atlas
POSTGRES_PASSWORD=atlas123
POSTGRES_DB=atlas

# AI API (Gemini)
AI_API_KEY=your-gemini-api-key-here
AI_MODEL=gemma2:2b

# Email
ATLAS_MANAGER_EMAIL=mohamad.j1380@yahoo.com
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=mohamad.j1380@yahoo.com
SMTP_PASS=yfryircolbfmfpzz

# Ollama (local transcription)
TRANSCRIPTION_API_URL=http://host.docker.internal:11434/v1/audio/transcriptions
```

---

## دسترسی به سرویس‌ها

| سرویس | URL | احراز هویت |
|-------|-----|-----------|
| Panel | http://mmdjolan.ir:8080 | بدون رمز (تنظیم در .env) |
| n8n | http://mmdjolan.ir:5678 | `mmdjolan` / `jolan1380` |
| PostgreSQL | localhost:15432 | `atlas` / `atlas123` |

---

## ادغام با سایت اصلی

### صفحات فعلی

سایت اصلی: `F:/atlas project/mmdjolan.ir/public_html/`

```
atlas_project/
├── upload.html          ✅ آپلود فایل صوتی
├── dashboard.html       ✅ داشبورد تحلیلی
├── workflows.html       ✅ مدیریت n8n
├── architecture.html    ✅ معماری
└── index.html          ✅ redirect به atlas-project.html
```

### JavaScript API Client

فایل: `js/atlas.js`

```javascript
const ATLAS_API = `http://${window.location.hostname}:8080`;

// Dashboard stats
fetch(`${ATLAS_API}/api/stats`)

// Upload voice
fetch(`${ATLAS_API}/api/upload-voice`, {
  method: 'POST',
  body: formData
})
```

### لینک‌های فعال

- صفحه اصلی پروژه: `http://mmdjolan.ir/atlas-project.html`
- آپلود: `http://mmdjolan.ir/atlas_project/upload.html`
- داشبورد: `http://mmdjolan.ir/atlas_project/dashboard.html`

---

## n8n Workflows

### ورک‌فلوهای فعال

1. **Atlas Call Intelligence v1**
   - Webhook: `/webhook/atlas/call-intelligence`
   - ورودی: transcript, agent_name, customer_name
   - خروجی: تحلیل کامل + ذخیره DB + ایمیل

2. **Monthly Report**
   - Webhook: `/webhook/atlas/call-intelligence/monthly-report`
   - اجرا: روز اول ماه (cron)
   - خروجی: گزارش ماهانه مدیریتی

### تست Webhook

```bash
curl -X POST http://localhost:5678/webhook/atlas/call-intelligence \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "test-001",
    "transcript": "اپراتور: سلام. مشتری: سلام، نرم‌افزار میخوام.",
    "agent_name": "علی",
    "customer_name": "آقای احمدی",
    "department": "sales"
  }'
```

---

## پایگاه داده

### جداول اصلی

```sql
-- تحلیل تماس‌ها
SELECT call_id, customer_name, purchase_intent_score, satisfaction_final_score
FROM call_analyses
ORDER BY analyzed_at DESC
LIMIT 10;

-- گزارش‌های ماهانه
SELECT * FROM monthly_reports
ORDER BY report_month DESC;

-- تنظیمات پنل
SELECT * FROM panel_settings;

-- قوانین هشدار
SELECT * FROM alert_rules;
```

### داده‌های نمونه

5 تماس نمونه در DB موجود است (از `002_panel_seed.sql`).

---

## عیب‌یابی

### Panel در دسترس نیست

```bash
# بررسی وضعیت
docker compose ps

# مشاهده لاگ
docker logs atlas-panel -f

# Restart
docker compose restart panel
```

### خطای دیتابیس

```bash
# بررسی health
docker exec atlas-postgres pg_isready -U atlas

# اجرای مجدد init scripts
docker exec -i atlas-postgres psql -U atlas -d atlas < docker/postgres/init/001_call_intelligence.sql
```

### n8n نمی‌تواند به DB متصل شود

بررسی کنید `postgres` سالم باشد:

```bash
docker compose ps postgres
# باید (healthy) نشان دهد
```

---

## فایل‌های کلیدی

```
F:/atlas project/
├── docker/
│   ├── docker-compose.yml       # تعریف سرویس‌ها
│   ├── .env                     # تنظیمات محیط
│   ├── panel/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI app
│   │   │   ├── queries.py      # SQL queries
│   │   │   ├── db.py           # PostgreSQL connection
│   │   │   ├── ai.py           # Gemini insights
│   │   │   └── transcribe.py   # Audio transcription
│   │   ├── templates/          # Jinja2 HTML
│   │   └── static/             # CSS/JS برای پنل
│   ├── postgres/init/
│   │   ├── 001_call_intelligence.sql  # Schema
│   │   ├── 002_panel_seed.sql         # Sample data
│   │   └── 003_panel_settings.sql     # Settings tables
│   ├── n8n/
│   │   ├── data/               # n8n storage
│   │   └── workflows/          # JSON workflows
│   └── mailer/
│       └── mailer.py           # SMTP service
└── mmdjolan.ir/public_html/
    ├── atlas-project.html      # صفحه هاب
    ├── atlas_project/          # زیرصفحات
    ├── js/
    │   ├── app.js              # اصلی سایت
    │   └── atlas.js            # API client
    └── css/
        └── style.css           # استایل یکپارچه
```

---

## چک‌لیست راه‌اندازی

- [ ] Docker services running: `docker compose ps`
- [ ] Panel accessible: `curl http://localhost:8080/api/stats`
- [ ] n8n accessible: http://localhost:5678 (mmdjolan/jolan1380)
- [ ] Database seeded: `docker exec atlas-postgres psql -U atlas -d atlas -c "SELECT COUNT(*) FROM call_analyses;"`
- [ ] Site pages working: http://mmdjolan.ir/atlas-project.html
- [ ] Upload page connects to panel: http://mmdjolan.ir/atlas_project/upload.html
- [ ] Dashboard loads stats: http://mmdjolan.ir/atlas_project/dashboard.html

---

## دستورات سریع

```bash
# Start all services
cd "F:/atlas project/docker" && docker compose up -d

# Stop all
docker compose down

# Restart panel only
docker compose restart panel

# View all logs
docker compose logs -f

# Access database
docker exec -it atlas-postgres psql -U atlas -d atlas

# Backup database
docker exec atlas-postgres pg_dump -U atlas atlas > backup_$(date +%Y%m%d).sql
```

---

✅ **پروژه آماده است.** پس از `docker compose up -d panel`، تمام سرویس‌ها باید فعال باشند.
