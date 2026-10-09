"""Render every panel template with sample data to catch Jinja errors before deploying."""
import sys
from datetime import datetime, date, timezone
from decimal import Decimal
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
PANEL = Path(__file__).resolve().parents[1] / "panel"
sys.path.insert(0, str(PANEL))

from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined  # noqa: E402
from app import fmt  # noqa: E402

env = Environment(loader=FileSystemLoader(str(PANEL / "templates")), autoescape=select_autoescape(["html"]))
fmt.register(env)


def fmt_duration(seconds):
    if not seconds:
        return "—"
    m, s = divmod(int(seconds), 60)
    return fmt.fa(f"{m}:{s:02d}")


env.globals.update(fmt_duration=fmt_duration, now_fn=datetime.now,
                   roles={"admin": "مدیر سیستم", "manager": "مدیر", "viewer": "مشاهده‌گر"})

now = datetime.now(timezone.utc)
user = {"id": 1, "username": "admin", "full_name": "محمد", "role": "admin", "is_active": True,
        "created_at": now, "last_login_at": now}
brand = {"company_name": "آتیران", "company_tagline": "هوش تماس", "brand_color": "#0ea5e9", "logo_data": ""}
analysis = {
    "executive_summary": "مشتری برای خرید ۲۰ دستگاه استعلام گرفت.",
    "next_actions": ["ارسال پیش‌فاکتور تا فردا", {"action": "تماس پیگیری", "owner": "فروش"}],
    "customer": {"request_summary": "استعلام قیمت", "needs": ["قیمت"], "pain_points": ["زمان تحویل"],
                 "satisfaction": {"initial_score": 60, "final_score": 80}, "sentiment": {"overall": "positive"}},
    "agent_performance": {"response_quality_score": 85, "strengths": ["صبور"], "improvements": ["پیگیری"]},
    "sales_analysis": {"applicable": True, "purchase_intent_score": 85, "purchase_stage": "decision",
                       "estimated_close_probability_percent": 70, "main_objections": ["قیمت"]},
    "support_analysis": {"applicable": False},
    "ticket": {"priority": "high", "follow_up_date": "2026-10-10", "tags": ["فروش"]},
    "insights": {"key_takeaways": ["مشتری جدی"], "risks": ["رقیب"], "opportunities": ["فروش عمده"]},
    "quality_control": {"needs_human_review": True, "review_reason": "مبلغ بالا"},
}
call = {"call_id": "web-1", "customer_name": "علی", "customer_phone": "09121234567", "agent_name": "سارا",
        "department": "sales", "call_date": now, "call_duration_seconds": 420, "transcript_text":
        "اپراتور: سلام\nمشتری: سلام، قیمت؟\nبدون گوینده", "purchase_intent_score": 85,
        "satisfaction_final_score": 80, "agent_quality_score": 90, "ticket_priority": "high",
        "needs_human_review": True, "analysis_json": analysis}
row = {**call, "next_step": "ارسال پیش‌فاکتور", "close_prob": "70", "resolution_status": "resolved",
       "retention_risk": "high", "purchase_stage": "decision"}
agent = {"agent_name": "سارا", "agent_id": None, "department": "sales", "total_calls": 4,
         "avg_quality": Decimal("82.5"), "avg_satisfaction": Decimal("75.0"), "avg_intent": Decimal("66.0"),
         "hot_leads": 2, "happy_customers": 3, "success_score": Decimal("78.8"), "sales_calls": 3,
         "support_calls": 1, "review_count": 1, "satisfied_count": 3, "unhappy_count": 1,
         "satisfaction_rate_percent": Decimal("75.0"), "total_seconds": 1200, "avg_seconds": Decimal("300"),
         "max_seconds": Decimal("600")}
monthly = {"meta": {}, "department_stats": {"sales": {"total_calls": 3, "avg_satisfaction": 70,
           "avg_agent_quality": 80, "success_rate_percent": 66}},
           "agent_rankings": [{"agent_name": "سارا", "success_score": 80, "total_calls": 3, "avg_agent_quality": 80,
                               "avg_satisfaction": 70, "avg_purchase_intent": 60, "needs_review_count": 0}],
           "executive": {"executive_summary": "ماه خوبی بود.", "recommendations": ["آموزش"],
                         "kpi_highlights": {"best_agent": "سارا"}, "department_insights": {"sales": "خوب"}}}

base = {"request": None, "user": user, "brand": brand, "can": lambda a: True, "active": ""}
cases = {
    "login.html": {"next": "/", "error": "1", "logged_out": False},
    "error.html": {"code": 404},
    "dashboard.html": {"stats": {"total_calls": 5, "avg_satisfaction": Decimal("71.2"), "total_talk_seconds": 900},
                       "top": [agent], "recent": [call], "departments": [{"department": "sales", "total": 3}],
                       "trend": [{"day": date.today(), "calls": 2, "avg_satisfaction": Decimal("70"), "avg_intent": None}],
                       "ranges": {"7": "۷ روز اخیر", "": "همه زمان‌ها"}, "current_range": "7"},
    "upload.html": {"max_mb": 50},
    "call_detail.html": {"call": call, "view": fmt.analysis_view(analysis)},
    "search.html": {"results": [row], "q": "علی"},
    "ready_to_buy.html": {"items": [row], "page": 1, "q": ""},
    "unhappy_customers.html": {"items": [row], "page": 2, "q": "x"},
    "successful_sales.html": {"items": [], "page": 1, "q": ""},
    "top_performers.html": {"items": [agent, agent, agent, agent]},
    "staff_performance.html": {"items": [agent]},
    "satisfaction.html": {"items": [agent]},
    "call_duration.html": {"items": [agent]},
    "monthly_reports.html": {"items": [{"id": 1, "report_month": date(2026, 9, 1), "department": "all",
                                        "total_calls": 3, "created_at": now}]},
    "monthly_detail.html": {"report": {"report_month": date(2026, 9, 1), "total_calls": 3, "created_at": now},
                            "data": monthly},
    "ai_insights.html": {},
    "settings.html": {"settings": {**brand, "notify_emails": "a@b.c", "notify_mode": "all"},
                      "rules": [{"id": 1, "name": "x", "rule_type": "low_satisfaction", "threshold": 40,
                                 "time_window_minutes": 60, "enabled": True}], "saved": "1", "error": ""},
    "users.html": {"users": [user, {**user, "id": 2, "username": "ali", "role": "viewer"}], "msg": "created"},
    "account.html": {"msg": "ok"},
}

failed = 0
out_dir = Path(__file__).resolve().parent / "_render"
out_dir.mkdir(exist_ok=True)
for name, extra in cases.items():
    try:
        html = env.get_template(name).render(**base, **extra)
        (out_dir / name).write_text(html, encoding="utf-8")
        bad = [m for m in ("{{", "{%", "None", "Undefined") if m in html.replace("{{ icon", "")]
        print(f"OK   {name:26} {len(html):>7} bytes" + (f"  suspicious: {bad}" if bad else ""))
    except Exception as exc:
        failed += 1
        print(f"FAIL {name:26} {type(exc).__name__}: {exc}")
try:
    from app import notify
    subject, html, text = notify.build_email(call, {"company_name": "آتیران", "brand_color": "#0ea5e9"}, env)
    (out_dir / "email.html").write_text(html, encoding="utf-8")
    print(f"OK   email                      {len(html):>7} bytes  subject: {subject}")
    print(text)
except Exception as exc:
    failed += 1
    print(f"FAIL email {type(exc).__name__}: {exc}")
sys.exit(1 if failed else 0)
