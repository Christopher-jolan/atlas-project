"""Display helpers: Jalali dates, Persian digits, enum labels, analysis view-model."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

LABELS = {
    "department": {"sales": "فروش", "support": "پشتیبانی", "mixed": "ترکیبی", "unknown": "نامشخص", "auto": "خودکار", "all": "همه بخش‌ها"},
    "priority": {"low": "کم", "medium": "متوسط", "high": "بالا", "urgent": "فوری"},
    "sentiment": {"positive": "مثبت", "neutral": "خنثی", "negative": "منفی", "mixed": "متغیر"},
    "level": {"low": "کم", "medium": "متوسط", "high": "زیاد"},
    "resolution": {"resolved": "حل‌شده", "partial": "تا حدی حل‌شده", "partially_resolved": "تا حدی حل‌شده", "unresolved": "حل‌نشده", "escalated": "ارجاع‌شده", "pending": "در انتظار"},
    "stage": {"awareness": "آشنایی", "interest": "علاقه‌مندی", "consideration": "در حال بررسی", "evaluation": "ارزیابی", "decision": "تصمیم‌گیری", "negotiation": "مذاکره", "purchase": "خرید", "closed": "بسته‌شده", "closed_won": "فروش موفق", "closed_lost": "از دست رفته"},
    "quality": {"good": "خوب", "fair": "متوسط", "poor": "ضعیف", "unknown": "نامشخص"},
    "direction": {"inbound": "ورودی", "outbound": "خروجی"},
}


def fa(value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        value = f"{value:.1f}".rstrip("0").rstrip(".")
    return str(value).translate(_FA_DIGITS)


def label(value, kind: str) -> str:
    if value is None or value == "":
        return "—"
    return LABELS.get(kind, {}).get(str(value).lower(), str(value))


def _gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def _to_local(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, datetime) and value.tzinfo:
        value = value.astimezone(TEHRAN)
    return value


def jdate(value, with_time: bool = False, long: bool = False) -> str:
    value = _to_local(value)
    if not isinstance(value, (date, datetime)):
        return "—"
    jy, jm, jd = _gregorian_to_jalali(value.year, value.month, value.day)
    text = f"{jd} {_JALALI_MONTHS[jm - 1]} {jy}" if long else f"{jy}/{jm:02d}/{jd:02d}"
    if with_time and isinstance(value, datetime):
        text += f" — {value.hour:02d}:{value.minute:02d}"
    return fa(text)


def jmonth(value) -> str:
    value = _to_local(value)
    if not isinstance(value, (date, datetime)):
        return "—"
    jy, jm, _ = _gregorian_to_jalali(value.year, value.month, 15)
    return fa(f"{_JALALI_MONTHS[jm - 1]} {jy}")


def score_tone(value) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "muted"
    return "good" if v >= 70 else "mid" if v >= 45 else "bad"


def _texts(items) -> list[str]:
    """Normalize a list whose items may be strings or small dicts into display strings."""
    out = []
    for item in items or []:
        if isinstance(item, str):
            if item.strip():
                out.append(item.strip())
        elif isinstance(item, dict):
            parts = [str(v) for v in item.values() if v not in (None, "", [], {})]
            if parts:
                out.append(" — ".join(parts))
        elif item is not None:
            out.append(str(item))
    return out


def analysis_view(a: dict | None) -> dict:
    """Flatten the stored analysis JSON into the fields the UI and emails display."""
    a = a or {}
    customer = a.get("customer") or {}
    sat = customer.get("satisfaction") or {}
    sentiment = customer.get("sentiment") or {}
    agent = a.get("agent_performance") or {}
    sales = a.get("sales_analysis") or {}
    support = a.get("support_analysis") or {}
    ticket = a.get("ticket") or {}
    insights = a.get("insights") or {}
    qc = a.get("quality_control") or {}

    actions = _texts(a.get("next_actions"))
    if not actions:
        actions = _texts([sales.get("recommended_next_step"), ticket.get("title") if ticket.get("actionable") else None])

    return {
        "summary": a.get("executive_summary") or customer.get("request_summary") or ticket.get("description") or "",
        "request": customer.get("request_summary") or "",
        "sms_brief": (a.get("sms_brief") or "").strip(),
        "actions": actions,
        "follow_up_date": ticket.get("follow_up_date") or "",
        "needs": _texts(customer.get("needs")),
        "pain_points": _texts(customer.get("pain_points")),
        "products": _texts(customer.get("products_mentioned")),
        "sentiment": label(sentiment.get("overall"), "sentiment"),
        "sat_initial": sat.get("initial_score"),
        "sat_final": sat.get("final_score"),
        "agent": {
            "quality": agent.get("response_quality_score"),
            "communication": agent.get("communication_skills"),
            "knowledge": agent.get("product_knowledge"),
            "empathy": agent.get("empathy_score"),
            "process": agent.get("process_adherence"),
            "strengths": _texts(agent.get("strengths")),
            "improvements": _texts(agent.get("improvements")),
        },
        "sales": {
            "applicable": bool(sales.get("applicable")),
            "intent": sales.get("purchase_intent_score"),
            "stage": label(sales.get("purchase_stage"), "stage"),
            "close_prob": sales.get("estimated_close_probability_percent"),
            "discount": sales.get("estimated_discount_to_close_percent"),
            "price_sensitivity": label(sales.get("price_sensitivity"), "level"),
            "objections": _texts(sales.get("main_objections")),
            "competitors": _texts(sales.get("competitor_mentions")),
            "next_step": sales.get("recommended_next_step") or "",
        },
        "support": {
            "applicable": bool(support.get("applicable")),
            "category": support.get("issue_category") or "",
            "issue": support.get("issue_summary") or "",
            "resolution": label(support.get("resolution_status"), "resolution"),
            "fcr": support.get("first_call_resolution"),
            "risk": label(support.get("customer_retention_risk"), "level"),
        },
        "ticket": {
            "title": ticket.get("title") or "",
            "priority": ticket.get("priority") or "",
            "description": ticket.get("description") or "",
            "assignee": ticket.get("recommended_assignee") or "",
            "tags": _texts(ticket.get("tags")),
        },
        "takeaways": _texts(insights.get("key_takeaways")),
        "risks": _texts(insights.get("risks")),
        "opportunities": _texts(insights.get("opportunities")),
        "compliance": _texts(insights.get("compliance_notes")),
        "review_reason": qc.get("review_reason") or "",
        "confidence": (a.get("meta") or {}).get("confidence_overall"),
    }


def register(env) -> None:
    env.filters.update(fa=fa, label=label, jdate=jdate, jmonth=jmonth, tone=score_tone)
    env.globals.update(analysis_view=analysis_view)
