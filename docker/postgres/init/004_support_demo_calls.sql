-- نمونه تماس‌های پشتیبانی برای نمایش در داشبورد (قابل اجرای مجدد با ON CONFLICT)
INSERT INTO call_analyses (
  call_id, department, agent_id, agent_name, customer_phone, customer_name,
  call_date, call_direction, call_duration_seconds, transcript_text, analysis_json,
  purchase_intent_score, satisfaction_final_score, agent_quality_score,
  ticket_priority, needs_human_review
) VALUES
(
  'demo-support-printer-lock',
  'support',
  'agent-sup-01',
  'مریم احمدی',
  '09121234001',
  'فروشگاه رضایی',
  NOW() - INTERVAL '18 hours',
  'inbound',
  512,
  'تماس پشتیبانی: خطای قفل سخت‌افزاری روی پرینتر فروشگاه.',
  '{
    "executive_summary": "مشتری هنگام چاپ فاکتور با خطای قفل سخت‌افزاری پرینتر مواجه شده بود. پشتیبان مراحل ریست قفل و بررسی اتصال را گام‌به‌گام انجام داد و پس از ریست، پرینتر بدون خطا کار کرد.",
    "department": "support",
    "customer": {
      "request_summary": "رفع خطای قفل سخت‌افزاری پرینتر",
      "satisfaction": { "final_score": 88, "initial_score": 52, "satisfied": true },
      "sentiment": { "overall": "positive" }
    },
    "support_analysis": {
      "applicable": true,
      "resolution_status": "resolved",
      "customer_retention_risk": "low"
    },
    "agent_performance": {
      "name": "مریم احمدی",
      "response_quality_score": 91,
      "communication_skills": "good",
      "empathy_score": 86
    },
    "sales_analysis": { "applicable": false, "purchase_intent_score": 8 },
    "ticket": { "priority": "medium", "actionable": false },
    "quality_control": { "needs_human_review": false },
    "next_actions": ["ثبت یادداشت ریست قفل در پرونده مشتری", "پیگیری تماس ۴۸ ساعته در صورت تکرار خطا"]
  }'::jsonb,
  8, 88, 91, 'medium', false
),
(
  'demo-support-printer',
  'support',
  'agent-sup-02',
  'رضا کریمی',
  '09129876002',
  'شرکت پارس چاپ',
  NOW() - INTERVAL '2 days',
  'inbound',
  438,
  'تماس پشتیبانی: مشکل چاپ و عدم شناسایی پرینتر توسط نرم‌افزار.',
  '{
    "executive_summary": "مشتری نمی‌توانست از نرم‌افزار به پرینتر شبکه‌ای چاپ بگیرد. پشتیبان درایور را بازنشانی کرد، پورت و سرویس Print Spooler را بررسی کرد و پس از تست، چاپ با موفقیت انجام شد.",
    "department": "support",
    "customer": {
      "request_summary": "مشکل پرینتر و عدم چاپ فاکتور",
      "satisfaction": { "final_score": 85, "initial_score": 48, "satisfied": true },
      "sentiment": { "overall": "positive" }
    },
    "support_analysis": {
      "applicable": true,
      "resolution_status": "resolved",
      "customer_retention_risk": "low"
    },
    "agent_performance": {
      "name": "رضا کریمی",
      "response_quality_score": 89,
      "communication_skills": "good",
      "empathy_score": 84
    },
    "sales_analysis": { "applicable": false, "purchase_intent_score": 5 },
    "ticket": { "priority": "low", "actionable": false },
    "quality_control": { "needs_human_review": false },
    "next_actions": ["ارسال راهنمای PDF تنظیم پرینتر شبکه", "بستن تیکت پس از تأیید مشتری"]
  }'::jsonb,
  5, 85, 89, 'low', false
),
(
  'demo-support-return-invoice',
  'support',
  'agent-sup-01',
  'مریم احمدی',
  '09125559003',
  'علی محمدی',
  NOW() - INTERVAL '5 days',
  'inbound',
  595,
  'تماس پشتیبانی: آموزش ثبت فاکتور برگشتی از فروش.',
  '{
    "executive_summary": "مشتری نحوه ثبت فاکتور برگشتی و اصلاح موجودی را نمی‌دانست. پشتیبان مسیر منو، انتخاب سند برگشت، و تأیید نهایی را آموزش داد و مشتری توانست عملیات را خودش انجام دهد.",
    "department": "support",
    "customer": {
      "request_summary": "آموزش ثبت فاکتور برگشتی",
      "satisfaction": { "final_score": 92, "initial_score": 70, "satisfied": true },
      "sentiment": { "overall": "positive" }
    },
    "support_analysis": {
      "applicable": true,
      "resolution_status": "resolved",
      "customer_retention_risk": "low"
    },
    "agent_performance": {
      "name": "مریم احمدی",
      "response_quality_score": 94,
      "communication_skills": "good",
      "empathy_score": 90
    },
    "sales_analysis": { "applicable": false, "purchase_intent_score": 12 },
    "ticket": { "priority": "low", "actionable": false },
    "quality_control": { "needs_human_review": false },
    "next_actions": ["ارسال لینک ویدیوی آموزشی فاکتور برگشتی", "دعوت به وبینار آموزشی ماهانه"]
  }'::jsonb,
  12, 92, 94, 'low', false
)
ON CONFLICT (call_id) DO UPDATE SET
  department = EXCLUDED.department,
  agent_name = EXCLUDED.agent_name,
  customer_name = EXCLUDED.customer_name,
  call_date = EXCLUDED.call_date,
  call_duration_seconds = EXCLUDED.call_duration_seconds,
  transcript_text = EXCLUDED.transcript_text,
  analysis_json = EXCLUDED.analysis_json,
  purchase_intent_score = EXCLUDED.purchase_intent_score,
  satisfaction_final_score = EXCLUDED.satisfaction_final_score,
  agent_quality_score = EXCLUDED.agent_quality_score,
  ticket_priority = EXCLUDED.ticket_priority,
  needs_human_review = EXCLUDED.needs_human_review,
  analyzed_at = NOW();
