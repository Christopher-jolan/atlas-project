"""SMS gateways (Ghasedak SMS REST/SOAP, ghasedak.me): sending, opt-out suffix, mobile detection and log."""
import html
import logging
import re
import uuid
from xml.sax.saxutils import escape

import httpx

from .db import execute, fetch_all, fetch_one

log = logging.getLogger("atlas.sms")

API_BASE = "https://gateway.ghasedak.me/rest/api/v1/WebService"
SOAP_URL = "https://panel.ghasedaksms.com/webservice/v2.asmx"
IRANSMS_BASE = "http://api.iransmsservice.com/v2"
DEFAULT_PROVIDER = "iransms"
LINE_RETRY_CODES = {7, 20, 29}
SOAP_ERRORS = {
    1: "نام کاربری یا رمز عبور وب‌سرویس پیامک معتبر نیست.",
    2: "آرایه‌ها خالی است.",
    3: "طول آرایه بیشتر از ۱۰۰ است.",
    4: "طول آرایه فرستنده، گیرنده و متن یکسان نیست.",
    5: "امکان گرفتن پیام جدید وجود ندارد.",
    6: "حساب کاربری یا وب‌سرویس غیرفعال است؛ رمز وب‌سرویس را در پنل پیامک دوباره تنظیم کنید.",
    7: "دسترسی به این خط ارسال وجود ندارد.",
    8: "شماره گیرنده نامعتبر است.",
    9: "اعتبار حساب پیامک کافی نیست.",
    10: "خطای موقت در سامانه پیامک؛ دوباره تلاش کنید.",
    11: "آی‌پی سرور در سامانه پیامک مجاز نیست.",
    20: "گیرنده پیامک تبلیغاتی را مسدود کرده است؛ برای او خط خدماتی لازم است.",
    29: "شماره خط ارسال در سامانه پیدا نشد.",
    21: "ارتباط با سرویس‌دهنده پیامک قطع است.",
    24: "این سرویس در پلن رایگان قابل استفاده نیست.",
}
# Carriers reject promotional SMS without the opt-out keyword at the very end.
OPT_OUT = "لغو11"
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_MOBILE = re.compile(r"^(?:\+?98|0098|0)?(9\d{9})$")


def normalize_mobile(raw) -> str | None:
    """Return an Iranian mobile as 09xxxxxxxxx, or None for landlines/invalid numbers."""
    if not raw:
        return None
    digits = re.sub(r"[\s\-()]", "", str(raw).translate(_DIGITS))
    m = _MOBILE.match(digits)
    return f"0{m.group(1)}" if m else None


def parse_numbers(value: str) -> list[str]:
    numbers = []
    for part in re.split(r"[,،;\s]+", value or ""):
        mobile = normalize_mobile(part)
        if mobile and mobile not in numbers:
            numbers.append(mobile)
    return numbers


def with_opt_out(text: str) -> str:
    text = (text or "").strip()
    if text.endswith(OPT_OUT):
        text = text[: -len(OPT_OUT)].rstrip()
    return f"{text}\n{OPT_OUT}" if text else OPT_OUT


def parts(text: str) -> int:
    unicode = any(ord(c) > 127 for c in text)
    single, multi = (70, 67) if unicode else (160, 153)
    n = len(text)
    return 1 if n <= single else -(-n // multi)


def fit(lines: list[str], limit: int) -> str:
    """Join lines and trim the longest trailing line so text + opt-out stays within `limit` chars."""
    budget = limit - len(OPT_OUT) - 1
    text = "\n".join(l for l in lines if l)
    if len(text) <= budget:
        return text
    head = "\n".join(l for l in lines[:-1] if l)
    room = budget - len(head) - 1
    tail = lines[-1]
    if room > 8:
        return f"{head}\n{tail[: room - 1].rstrip()}…"
    return text[: budget - 1].rstrip() + "…"


def recently_sent(receptor: str, kind: str, hours: int = 24) -> bool:
    return bool(fetch_one(
        "SELECT 1 FROM sms_log WHERE receptor = %s AND kind = %s AND success "
        "AND created_at > NOW() - (%s || ' hours')::interval LIMIT 1",
        (receptor, kind, str(hours)),
    ))


def recent_log(limit: int = 15) -> list[dict]:
    return fetch_all(
        "SELECT created_at, kind, receptor, message, success, error, call_id FROM sms_log ORDER BY id DESC LIMIT %s",
        (limit,),
    )


def _log(kind, receptor, message, success, message_id="", error="", call_id=None):
    try:
        execute(
            "INSERT INTO sms_log (kind, receptor, message, success, message_id, error, call_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (kind, receptor, message, success, message_id, (error or "")[:500], call_id),
        )
    except Exception:
        log.exception("Could not write sms_log")


def provider(settings: dict) -> str:
    return settings.get("sms_provider") or DEFAULT_PROVIDER


def configured(settings: dict) -> bool:
    if provider(settings) == "ghasedaksms":
        return bool(settings.get("sms_username") and settings.get("sms_password"))
    return bool(settings.get("sms_api_key"))


def lines(settings: dict) -> list[str]:
    return [l for l in re.split(r"[,،;\s]+", settings.get("sms_line_number", "")) if l]


async def _send_iransms(settings: dict, mobile: str, message: str) -> tuple[bool, str, str]:
    """Try each configured line in order; a blocked line or filtered recipient falls through to the next."""
    error = "شماره خط ارسال تنظیم نشده است."
    for line in lines(settings):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{IRANSMS_BASE}/sms/send/simple",
                headers={"apikey": settings.get("sms_api_key", "")},
                data={"message": message, "sender": line, "receptor": mobile},
            )
        try:
            data = resp.json()
        except ValueError:
            return False, "", "کلید API پیامک معتبر نیست." if not resp.text.strip() else f"HTTP {resp.status_code}"
        code = data.get("messageids")
        if not (isinstance(code, (int, float)) or str(code).lstrip("-").isdigit()):
            return False, "", data.get("message") or "پاسخ نامعتبر از سامانه پیامک."
        code = int(code)
        if code > 1000:
            return True, str(code), ""
        error = SOAP_ERRORS.get(code, f"خطای سامانه پیامک (کد {code})") + f" (خط {line})"
        if code not in LINE_RETRY_CODES:
            break
    return False, "", error


async def _send_rest(settings: dict, mobile: str, message: str) -> tuple[bool, str, str]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_BASE}/SendSingleSMS",
            headers={"ApiKey": settings.get("sms_api_key", "")},
            json={"lineNumber": settings.get("sms_line_number", ""), "receptor": mobile, "message": message,
                  "clientReferenceId": uuid.uuid4().hex[:20]},
        )
    data = resp.json()
    ok = bool(data.get("isSuccess") or data.get("IsSuccess"))
    payload = data.get("data") or data.get("Data") or {}
    message_id = str(payload.get("messageId") or payload.get("MessageId") or "") if isinstance(payload, dict) else ""
    error = "" if ok else (data.get("message") or data.get("Message") or f"HTTP {resp.status_code}")
    return ok, message_id, error


async def _soap(action: str, body: str) -> str:
    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body>'
        f'<{action} xmlns="http://tempuri.org/">{body}</{action}></soap:Body></soap:Envelope>'
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            SOAP_URL, content=envelope.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f'"http://tempuri.org/{action}"'},
        )
    fault = re.search(r"<faultstring>(.*?)</faultstring>", resp.text, re.S)
    if fault:
        raise RuntimeError(html.unescape(fault.group(1)))
    return resp.text


def _auth(settings: dict) -> str:
    return (f"<username>{escape(settings.get('sms_username', ''))}</username>"
            f"<password>{escape(settings.get('sms_password', ''))}</password>")


async def _send_soap(settings: dict, mobile: str, message: str) -> tuple[bool, str, str]:
    xml = await _soap("SendSMS", _auth(settings) +
                      f"<senderNumbers><string>{escape(settings.get('sms_line_number', ''))}</string></senderNumbers>"
                      f"<recipientNumbers><string>{mobile}</string></recipientNumbers>"
                      f"<messageBodies><string>{escape(message)}</string></messageBodies>")
    m = re.search(r"<long>(-?\d+)</long>", xml)
    code = int(m.group(1)) if m else 0
    if code > 1000:
        return True, str(code), ""
    return False, "", SOAP_ERRORS.get(code, f"خطای سامانه پیامک (کد {code})")


async def send(settings: dict, receptor: str, text: str,
               kind: str = "manual", call_id: str | None = None) -> dict:
    message = with_opt_out(text)
    mobile = normalize_mobile(receptor)
    if not mobile:
        return {"success": False, "receptor": receptor, "error": "شماره موبایل معتبر نیست."}
    if not configured(settings):
        return {"success": False, "receptor": mobile, "error": "اطلاعات اتصال سامانه پیامک تنظیم نشده است."}
    sender = {"ghasedaksms": _send_soap, "ghasedak_me": _send_rest}.get(provider(settings), _send_iransms)
    try:
        ok, message_id, error = await sender(settings, mobile, message)
    except Exception as exc:
        log.exception("SMS request failed")
        ok, message_id, error = False, "", f"اتصال به سامانه پیامک برقرار نشد: {exc}"
    _log(kind, mobile, message, ok, message_id, error, call_id)
    if not ok:
        log.error("SMS to %s failed: %s", mobile, error)
    return {"success": ok, "receptor": mobile, "message_id": message_id, "error": error or None,
            "parts": parts(message)}


async def account_info(settings: dict) -> dict:
    if not configured(settings):
        return {"success": False, "error": "اطلاعات اتصال سامانه پیامک تنظیم نشده است."}
    try:
        if provider(settings) == "iransms":
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(f"{IRANSMS_BASE}/credit", headers={"apikey": settings.get("sms_api_key", "")})
            try:
                data = resp.json()
            except ValueError:
                return {"success": False, "error": "کلید API پیامک معتبر نیست."}
            if data.get("result") != "success":
                return {"success": False, "error": data.get("message") or "کلید API پیامک معتبر نیست."}
            return {"success": True, "credit": data.get("credit")}
        if provider(settings) == "ghasedaksms":
            xml = await _soap("GetCredit", _auth(settings))
            m = re.search(r"<GetCreditResult>(-?[\d.]+)</GetCreditResult>", xml)
            credit = float(m.group(1)) if m else -1
            if credit < 0:
                return {"success": False, "error": "نام کاربری یا رمز عبور وب‌سرویس پیامک معتبر نیست."}
            return {"success": True, "credit": credit}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{API_BASE}/GetAccountInformation",
                                    headers={"ApiKey": settings.get("sms_api_key", "")})
        data = resp.json()
    except Exception as exc:
        return {"success": False, "error": f"اتصال به سامانه پیامک برقرار نشد: {exc}"}
    ok = bool(data.get("isSuccess") or data.get("IsSuccess"))
    info = data.get("data") or data.get("Data") or {}
    return {"success": ok, "credit": info.get("credit") or info.get("Credit"),
            "error": None if ok else (data.get("message") or data.get("Message"))}
