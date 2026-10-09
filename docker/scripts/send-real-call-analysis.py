#!/usr/bin/env python3
"""Deep Persian call analysis with Gemini + email delivery."""
import json
import os
import re
import urllib.request
from pathlib import Path

API_KEY = os.getenv("AI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
MAILER_URL = "http://localhost:8765/send"
TO_EMAIL = "mohamad.j1380@yahoo.com"
TRANSCRIPT_PATH = Path(r"F:\atlas project\docker\scripts\real-call-transcript.txt")


def gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        GEMINI_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"]


def analyze_transcript(transcript: str) -> dict:
    prompt = f"""تو یک تحلیلگر حرفه‌ای تماس‌های فروش و پشتیبانی شرکت‌های نرم‌افزار حسابداری ایرانی (گروه آتی‌ران) هستی.

این رونوشت یک تماس واقعی است. فقط JSON معتبر برگردان (بدون markdown):

{{
  "department": "sales|support|mixed",
  "department_reason": "چرا این بخش",
  "customer_name": "",
  "customer_business": "",
  "agent_name": "",
  "call_summary": "خلاصه ۳-۴ جمله فارسی",
  "customer_needs": ["نیاز 1", "نیاز 2"],
  "customer_pain_points": ["درد 1"],
  "services_requested": ["خدمت 1"],
  "sales": {{
    "applicable": true,
    "purchase_intent_score": 0-100,
    "close_probability_percent": 0-100,
    "main_objections": [],
    "price_discussed": true/false,
    "estimated_discount_percent": null,
    "competitor_mentioned": false,
    "recommended_next_step": ""
  }},
  "support": {{
    "applicable": true/false,
    "issues_raised": [],
    "resolution_status": "resolved|partial|unresolved|not_applicable"
  }},
  "customer_satisfaction": {{
    "initial_score": 0-100,
    "final_score": 0-100,
    "satisfied": true/false,
    "reason": ""
  }},
  "agent_performance": {{
    "quality_score": 0-100,
    "strengths": [],
    "improvements": [],
    "suggested_actions": []
  }},
  "key_insights": [],
  "risks": [],
  "opportunities": [],
  "follow_up_required": true/false,
  "follow_up_action": "",
  "ticket_title": "",
  "ticket_priority": "low|medium|high"
}}

قوانین:
- همه متن‌ها فارسی
- دقیق و بر اساس متن تماس
- امتیازها واقع‌بینانه

رونوشت:
{transcript}
"""
    text = gemini(prompt)
    text = re.sub(r"^```json\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    return json.loads(text)


def build_email(a: dict, call_id: str) -> tuple[str, str]:
    dept = {"sales": "فروش", "support": "پشتیبانی", "mixed": "ترکیبی"}.get(a.get("department", ""), "نامشخص")
    sat = a.get("customer_satisfaction", {})
    sales = a.get("sales", {})
    agent = a.get("agent_performance", {})
    support = a.get("support", {})

    subject = f"[اطلس] تحلیل تماس {dept} — {a.get('customer_name') or a.get('customer_business') or call_id}"

    def bullets(items, prefix="  • "):
        return [f"{prefix}{x}" for x in items] if items else [f"{prefix}-"]

    lines = [
        "تحلیل تماس صوتی — Atlas Call Intelligence",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"شناسه تماس: {call_id}",
        f"بخش: {dept} — {a.get('department_reason', '')}",
        f"مشتری: {a.get('customer_name', '-')} ({a.get('customer_business', '-')})",
        f"اپراتور: {a.get('agent_name', 'نامشخص')}",
        "",
        "📋 خلاصه تماس",
        a.get("call_summary", "-"),
        "",
        "🎯 نیازهای مشتری",
        *bullets(a.get("customer_needs", [])),
        "",
        "⚠️ مشکلات / دغدغه‌ها (Pain Points)",
        *bullets(a.get("customer_pain_points", [])),
        "",
        "🛒 خدمات/محصولات مورد نیاز",
        *bullets(a.get("services_requested", [])),
        "",
        "😊 رضایت مشتری",
        f"  • اولیه: {sat.get('initial_score', 'N/A')}/100 → نهایی: {sat.get('final_score', 'N/A')}/100",
        f"  • راضی بود: {'بله ✅' if sat.get('satisfied') else 'خیر ❌'}",
        f"  • دلیل: {sat.get('reason', '-')}",
        "",
    ]

    if sales.get("applicable"):
        lines += [
            "💰 تحلیل فروش",
            f"  • نزدیکی به خرید: {sales.get('purchase_intent_score', 'N/A')}/100",
            f"  • احتمال بستن معامله: {sales.get('close_probability_percent', 'N/A')}%",
            f"  • اعتراضات: {', '.join(sales.get('main_objections', [])) or '-'}",
            f"  • قیمت مطرح شد: {'بله' if sales.get('price_discussed') else 'خیر'}",
            f"  • تخفیف پیشنهادی: {sales.get('estimated_discount_percent') or '-'}%",
            f"  • اقدام بعدی: {sales.get('recommended_next_step', '-')}",
            "",
        ]

    if support.get("applicable"):
        lines += [
            "🔧 تحلیل پشتیبانی",
            f"  • موضوعات: {', '.join(support.get('issues_raised', [])) or '-'}",
            f"  • وضعیت: {support.get('resolution_status', '-')}",
            "",
        ]

    lines += [
        "👤 عملکرد اپراتور",
        f"  • امتیاز کیفیت: {agent.get('quality_score', 'N/A')}/100",
        "  • نقاط قوت:",
        *([f"    + {x}" for x in agent.get("strengths", [])] or ["    + -"]),
        "  • قابل بهبود:",
        *([f"    - {x}" for x in agent.get("improvements", [])] or ["    - -"]),
        "  • اقدامات پیشنهادی ویزیتور/پشتیبان:",
        *([f"    → {x}" for x in agent.get("suggested_actions", [])] or ["    → -"]),
        "",
        "💡 بینش‌های کلیدی",
        *bullets(a.get("key_insights", [])),
        "",
        "🚨 ریسک‌ها",
        *bullets(a.get("risks", [])),
        "",
        "🌟 فرصت‌ها",
        *bullets(a.get("opportunities", [])),
        "",
        "📌 پیگیری",
        f"  • نیاز به پیگیری: {'بله' if a.get('follow_up_required') else 'خیر'}",
        f"  • اقدام: {a.get('follow_up_action', '-')}",
        f"  • تیکت: {a.get('ticket_title', '-')} | اولویت: {a.get('ticket_priority', '-')}",
        "",
        "— Atlas Call Intelligence | گروه اطلس",
    ]
    return subject, "\n".join(lines)


def send_email(subject: str, body: str) -> bool:
    payload = json.dumps({"to": TO_EMAIL, "subject": subject, "body": body}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        MAILER_URL,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("success") is True


def main() -> int:
    transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8")
    call_id = "atiran-real-call-001"
    print("Analyzing with Gemini 2.5 Flash...")
    analysis = analyze_transcript(transcript)
    Path(r"F:\atlas project\docker\scripts\real-call-analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    subject, body = build_email(analysis, call_id)
    print("Sending email...")
    ok = send_email(subject, body)
    print(f"EMAIL_SENT={ok}")
    print(f"department={analysis.get('department')}")
    print(f"purchase_intent={analysis.get('sales', {}).get('purchase_intent_score')}")
    print(f"satisfaction={analysis.get('customer_satisfaction', {}).get('final_score')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
