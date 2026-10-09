"""Manager notification emails: readable Persian report, never raw JSON."""
import logging

import httpx

from . import fmt, sms
from .config import MAILER_URL, PANEL_PUBLIC_URL

# Two concatenated Persian (UCS-2) SMS parts; keeps manager texts cheap and readable.
MANAGER_SMS_LIMIT = 134

log = logging.getLogger("atlas.notify")


def is_important(call: dict) -> bool:
    return bool(
        (call.get("purchase_intent_score") or 0) >= 70
        or (call.get("satisfaction_final_score") is not None and call["satisfaction_final_score"] < 60)
        or call.get("ticket_priority") in ("high", "urgent")
        or call.get("needs_human_review")
    )


def headline(call: dict) -> str:
    if call.get("ticket_priority") == "urgent" or call.get("needs_human_review"):
        return "نیاز به پیگیری فوری"
    if (call.get("purchase_intent_score") or 0) >= 70:
        return "مشتری آماده خرید"
    if call.get("satisfaction_final_score") is not None and call["satisfaction_final_score"] < 60:
        return "مشتری ناراضی"
    return f"تماس {fmt.label(call.get('department'), 'department')}"


def build_email(call: dict, settings: dict, templates) -> tuple[str, str, str]:
    view = fmt.analysis_view(call.get("analysis_json"))
    company = settings.get("company_name") or "اطلس"
    customer = call.get("customer_name") or call.get("customer_phone") or "مشتری"
    subject = f"{company} | {headline(call)}: {customer}"
    panel_link = f"{PANEL_PUBLIC_URL}/calls/{call['call_id']}" if PANEL_PUBLIC_URL else ""

    html = templates.get_template("email/analysis.html").render(
        call=call, v=view, company=company, headline=headline(call),
        color=settings.get("brand_color") or "#4f46e5", panel_link=panel_link,
    )

    lines = [
        f"گزارش تحلیل تماس — {company}",
        f"{headline(call)}",
        "",
        f"مشتری: {customer}",
        f"اپراتور: {call.get('agent_name') or '—'}",
        f"بخش: {fmt.label(call.get('department'), 'department')}",
        f"تاریخ: {fmt.jdate(call.get('call_date'), with_time=True)}",
        "",
        "خلاصه تماس:",
        view["summary"] or "—",
    ]
    if view["actions"]:
        lines += ["", "اقدامات پیش رو:"] + [f"{fmt.fa(i)}. {a}" for i, a in enumerate(view["actions"], 1)]
    lines += [
        "",
        f"قصد خرید: {fmt.fa(call.get('purchase_intent_score'))} از ۱۰۰",
        f"رضایت مشتری: {fmt.fa(call.get('satisfaction_final_score'))} از ۱۰۰",
        f"کیفیت اپراتور: {fmt.fa(call.get('agent_quality_score'))} از ۱۰۰",
    ]
    if call.get("needs_human_review") and view["review_reason"]:
        lines += ["", f"نیاز به بررسی مدیر: {view['review_reason']}"]
    if panel_link:
        lines += ["", f"گزارش کامل: {panel_link}"]
    return subject, html, "\n".join(lines)


def build_manager_sms(call: dict, settings: dict) -> str:
    view = fmt.analysis_view(call.get("analysis_json"))
    company = settings.get("company_name") or "اطلس"
    customer = call.get("customer_name") or call.get("customer_phone") or "ناشناس"
    action = view["sms_brief"] or (view["actions"][0] if view["actions"] else view["summary"])
    scores = f"خرید {fmt.fa(call.get('purchase_intent_score'))} | رضایت {fmt.fa(call.get('satisfaction_final_score'))}"
    text = sms.fit([
        f"{company} | {headline(call)}",
        f"مشتری: {customer}",
        scores,
        f"اقدام: {action}" if action else "",
    ], MANAGER_SMS_LIMIT)
    return sms.with_opt_out(text)


def sms_ready(settings: dict) -> bool:
    return settings.get("sms_enabled", "true") == "true" and sms.configured(settings)


async def sms_managers(settings: dict, text: str, kind: str, call_id: str | None = None) -> list[dict]:
    return [
        await sms.send(settings, n, text, kind, call_id)
        for n in sms.parse_numbers(settings.get("sms_manager_numbers", ""))
    ]


async def send_call_sms(call: dict, settings: dict) -> dict:
    if not sms_ready(settings):
        return {"skipped": "disabled"}
    out: dict = {}
    mode = settings.get("sms_manager_mode", "all")
    if mode == "all" or (mode == "important" and is_important(call)):
        out["manager"] = await sms_managers(settings, build_manager_sms(call, settings), "manager", call["call_id"])
    else:
        out["manager"] = f"mode_{mode}"

    mobile = sms.normalize_mobile(call.get("customer_phone"))
    if settings.get("sms_customer_enabled") != "true":
        out["customer"] = "disabled"
    elif not mobile:
        out["customer"] = "not_mobile"
    elif sms.recently_sent(mobile, "customer"):
        out["customer"] = "already_sent_24h"
    else:
        out["customer"] = await sms.send(
            settings, mobile, settings.get("sms_customer_text", ""), "customer", call["call_id"],
        )
    return out


async def send_mail(to: str, subject: str, text: str, html: str = "", from_name: str = "") -> dict:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{MAILER_URL}/send", json={
                "to": to, "subject": subject, "body": text, "html": html, "from_name": from_name,
            })
        return resp.json()
    except Exception as exc:
        log.exception("Mailer unreachable")
        return {"success": False, "error": str(exc)}
