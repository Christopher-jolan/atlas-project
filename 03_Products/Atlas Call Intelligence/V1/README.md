# Atlas Call Intelligence v1

تحلیل هوشمند تماس‌های صوتی برای شرکت‌های حسابداری — محصول **اطلس**.

## قابلیت‌ها

- دریافت فایل صوتی (URL) یا متن رونوشت
- تشخیص خودکار بخش **فروش** / **پشتیبانی** / **ترکیبی**
- خروجی JSON استاندارد و قابل کنترل (schema ثابت)
- تحلیل رضایت مشتری از روی لحن و محتوا
- ارزیابی عملکرد اپراتور (فروش یا پشتیبان)
- تولید تیکت CRM آماده (فعلاً ایمیل به مدیر)
- ذخیره در PostgreSQL برای گزارش‌گیری
- گزارش ماهانه عملکرد پرسنل و بخش‌ها

## معماری

```
Issabel (ضبط تماس) → پنل اطلس → Webhook n8n
                              ↓
                    Transcription API (fa)
                              ↓
                         AI Analysis
                              ↓
              PostgreSQL + Email Manager + JSON Response
                              ↓
              Monthly Report (Cron + Manual Webhook)
```

## نصب

### 1. Docker

```bash
cd docker
docker compose up -d
```

اگر PostgreSQL از قبل داده دارد، اسکیما را دستی اجرا کنید:

```bash
docker exec -i atlas-postgres psql -U atlas -d atlas < postgres/init/001_call_intelligence.sql
```

### 2. Import ورکفلوها در n8n

1. باز کنید: `http://localhost:5678`
2. Import کنید:
   - `docker/n8n/workflows/atlas-call-intelligence-v1.json`
   - `docker/n8n/workflows/atlas-call-intelligence-monthly-report.json`
3. Credential **Atlas PostgreSQL** بسازید:
   - Host: `postgres`
   - Database: `atlas`
   - User: `atlas`
   - Password: `atlas123`
   - Port: `5432`
4. (اختیاری) Credential **Atlas SMTP** برای ایمیل مدیر
5. Activate کنید

### 3. متغیرهای محیطی (`.env`)

```env
AI_API_URL=http://host.docker.internal:11434/v1/chat/completions
TRANSCRIPTION_API_URL=http://host.docker.internal:11434/v1/audio/transcriptions
AI_API_KEY=your-key
AI_MODEL=gpt-4o-mini
ATLAS_MANAGER_EMAIL=manager@company.com
ATLAS_SMTP_FROM=atlas@company.com
```

## API — تحلیل تماس

**POST** `http://localhost:5678/webhook/atlas/call-intelligence`

### ورودی

| فیلد | نوع | الزامی | توضیح |
|------|-----|--------|-------|
| `audioUrl` | string | یکی از دو | لینک فایل صوتی Issabel/پنل |
| `transcript` | string | یکی از دو | رونوشت آماده (رد transcription) |
| `call_id` | string | خیر | شناسه تماس |
| `department` | string | خیر | `sales` / `support` / `auto` |
| `agent_name` | string | خیر | نام اپراتور |
| `agent_id` | string | خیر | شناسه اپراتور |
| `customer_phone` | string | خیر | تلفن مشتری |
| `customer_name` | string | خیر | نام مشتری |
| `call_direction` | string | خیر | `inbound` / `outbound` |
| `call_duration_seconds` | number | خیر | مدت تماس |
| `call_date` | string | خیر | ISO8601 |
| `product_context` | string | خیر | زمینه کسب‌وکار |

### نمونه درخواست

```json
{
  "audioUrl": "https://panel.example.com/recordings/call-123.wav",
  "call_id": "call-123",
  "department": "sales",
  "agent_name": "علی رضایی",
  "agent_id": "agent-42",
  "customer_phone": "09121234567",
  "customer_name": "شرکت آلفا",
  "call_direction": "inbound",
  "call_duration_seconds": 420
}
```

### نمونه خروجی (خلاصه)

```json
{
  "success": true,
  "call_id": "call-123",
  "department": "sales",
  "stored_in_db": true,
  "analysis": {
    "meta": { "department": "sales", "confidence_overall": 87 },
    "transcript": { "full_text": "...", "segments": [] },
    "customer": {
      "request_summary": "درخواست خرید نرم‌افزار حسابداری",
      "satisfaction": { "initial_score": 45, "final_score": 72, "delta": 27 }
    },
    "sales_analysis": {
      "purchase_intent_score": 78,
      "estimated_discount_to_close_percent": 12,
      "estimated_close_probability_percent": 65
    },
    "ticket": {
      "title": "پیگیری پیش‌فاکتور با تخفیف ۱۲٪",
      "priority": "high",
      "actionable": true,
      "follow_up_required": true
    }
  },
  "manager_notification": {
    "subject": "[اطلس] تیکت فروش - ...",
    "body": "..."
  }
}
```

Schema کامل: [`schema.json`](./schema.json)

## API — گزارش ماهانه

**POST** `http://localhost:5678/webhook/atlas/call-intelligence/monthly-report`

```json
{ "year": 2026, "month": 7 }
```

بدون body → ماه قبل به‌صورت خودکار.

Cron: **اول هر ماه ساعت ۸ صبح** (Asia/Tehran)

### خروجی گزارش

- آمار هر بخش (فروش/پشتیبانی)
- رتبه‌بندی پرسنل
- برترین‌ها و نیازمند آموزش
- خلاصه مدیریتی AI + توصیه‌ها

## اتصال Issabel

1. Issabel تماس را ضبط می‌کند
2. پنل اطلس URL فایل + متادیتا را به Webhook می‌فرستد
3. n8n تحلیل می‌کند و تیکت ایمیل می‌شود
4. (آینده) API CRM به‌جای ایمیل

## کنترل کیفیت

- `quality_control.needs_human_review`: نیاز به بررسی انسان
- `quality_control.analysis_flags`: پرچم‌های هشدار
- امتیاز `confidence_overall`: اطمینان تحلیل

## ایده‌های اضافه‌شده

- **تحلیل churn risk** در پشتیبانی
- **تخمین تخفیف برای بستن معامله** در فروش
- **first_call_resolution** برای KPI پشتیبانی
- **insights.opportunities** برای upsell
- **insights.compliance_notes** برای مسائل حقوقی/مالی
- **رتبه‌بندی ماهانه پرسنل** با success_score

## فاز بعدی

- [ ] API CRM (ایجاد تیکت خودکار)
- [ ] داشبورد مدیریتی
- [ ] Real-time alert برای تماس‌های urgent
- [ ] Fine-tune مدل روی دامنه حسابداری ایران
