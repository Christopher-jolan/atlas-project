import base64
import csv
import io
import json
import logging
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import auth, fmt, migrations, notify, queries, sms
from .ai import generate_executive_insights
from .config import (
    UPLOAD_MAX_MB, API_TOKEN, RATE_LIMIT_RPM, CORS_ORIGINS,
    PUBLIC_DEMO_API, PANEL_PUBLIC_URL,
)
from .audio_meta import audio_duration_seconds
from .call_analysis import analyze_transcript
from .transcribe import transcribe_audio

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # request URLs carry the Gemini API key
log = logging.getLogger("atlas.panel")

BASE = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
fmt.register(templates.env)

app = FastAPI(title="Atlas Manager Panel", docs_url=None, redoc_url=None, openapi_url=None)

DEMO_ORIGINS = {
    "https://mmdjolan.ir",
    "https://www.mmdjolan.ir",
    "http://mmdjolan.ir",
    "http://www.mmdjolan.ir",
}
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
if "*" in origins or not origins:
    cors_origins = ["*"]
else:
    cors_origins = list(dict.fromkeys(origins + sorted(DEMO_ORIGINS)))
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".mp4", ".wav", ".ogg", ".webm", ".aac", ".flac"}
LOGO_TYPES = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
PUBLIC_API_PATHS = {"/api/stats", "/api/recent-calls", "/api/upload-voice", "/api/upload-batch"}


@app.on_event("startup")
def _startup():
    migrations.run()


# ── Rate limiting ────────────────────────────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate(key: str, limit: int, window: int = 60) -> bool:
    now = time.time()
    hits = _rate_store[key]
    hits[:] = [t for t in hits if now - t < window]
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


def _client_ip(request: Request) -> str:
    return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host


# ── Template context ─────────────────────────────────────────────
_brand_cache: dict = {"at": 0.0, "value": {}}


def brand() -> dict:
    if time.time() - _brand_cache["at"] > 10:
        _brand_cache["value"] = queries.get_settings()
        _brand_cache["at"] = time.time()
    return _brand_cache["value"]


def _invalidate_brand():
    _brand_cache["at"] = 0.0


class AtlasJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


templates.env.policies["json.dumps_kwargs"]["cls"] = AtlasJSONEncoder


def fmt_duration(seconds) -> str:
    if not seconds:
        return "—"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return fmt.fa(f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}")


templates.env.globals.update(
    fmt_duration=fmt_duration, now_fn=datetime.now, roles=auth.ROLES,
    asset_v=int((BASE / "static" / "css" / "style.css").stat().st_mtime),
)


def ctx(request: Request, **extra):
    user = getattr(request.state, "user", None)
    return {
        "request": request,
        "active": extra.pop("active", ""),
        "user": user,
        "brand": brand(),
        "can": lambda action: auth.can(user, action),
        **extra,
    }


def render(request: Request, name: str, status_code: int = 200, **extra):
    return templates.TemplateResponse(request, name, ctx(request, **extra), status_code=status_code)


def require(request: Request, action: str):
    if not auth.can(getattr(request.state, "user", None), action):
        raise HTTPException(403)


# ── Auth middleware ──────────────────────────────────────────────
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    request.state.user = None
    if path.startswith("/static") or path in ("/login", "/api/health", "/favicon.ico", "/robots.txt"):
        return await call_next(request)

    request.state.user = auth.user_from_session(request.cookies.get(auth.COOKIE_NAME))

    if path.startswith("/api/"):
        if request.state.user or request.method == "OPTIONS":
            return await call_next(request)
        if API_TOKEN and request.headers.get("X-API-Token") == API_TOKEN:
            return await call_next(request)
        if PUBLIC_DEMO_API and path in PUBLIC_API_PATHS:
            return await call_next(request)
        denied = JSONResponse({"detail": "برای دسترسی وارد پنل شوید."}, status_code=401)
        origin = request.headers.get("origin") or ""
        if origin and (cors_origins == ["*"] or origin in cors_origins or origin in DEMO_ORIGINS):
            denied.headers["Access-Control-Allow-Origin"] = origin
            denied.headers["Vary"] = "Origin"
        return denied

    if not request.state.user:
        target = path + (f"?{request.url.query}" if request.url.query else "")
        return RedirectResponse(f"/login?next={target}", status_code=302)
    return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/") or exc.status_code not in (403, 404):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return render(request, "error.html", status_code=exc.status_code, code=exc.status_code)


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return HTMLResponse("User-agent: *\nDisallow: /\n", media_type="text/plain")


# ── Login ────────────────────────────────────────────────────────
def _safe_next(target: str) -> str:
    return target if target.startswith("/") and not target.startswith("//") else "/"


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/", error: str = "", out: str = ""):
    if auth.user_from_session(request.cookies.get(auth.COOKIE_NAME)):
        return RedirectResponse(_safe_next(next), status_code=302)
    return render(request, "login.html", next=_safe_next(next), error=error, logged_out=bool(out))


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: str = Form(""),
    next: str = Form("/"),
):
    target = _safe_next(next)
    if not _check_rate(f"login:{_client_ip(request)}", 10, 600):
        return RedirectResponse(f"/login?error=rate&next={target}", status_code=302)
    user = auth.authenticate(username, password)
    if not user:
        return RedirectResponse(f"/login?error=1&next={target}", status_code=302)
    token, max_age = auth.make_session(user, remember == "on")
    resp = RedirectResponse(target, status_code=302)
    resp.set_cookie(
        auth.COOKIE_NAME, token, max_age=max_age, httponly=True, samesite="lax",
        secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https",
    )
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login?out=1", status_code=302)
    resp.delete_cookie(auth.COOKIE_NAME)
    return resp


# ── Dashboard & reports ──────────────────────────────────────────
DASHBOARD_RANGES = {"1": "امروز", "7": "۷ روز اخیر", "30": "۳۰ روز اخیر", "90": "۳ ماه اخیر", "": "همه زمان‌ها"}


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, range: str = ""):
    if range not in DASHBOARD_RANGES:
        range = ""
    date_from = None
    if range:
        start = datetime.now(fmt.TEHRAN).replace(hour=0, minute=0, second=0, microsecond=0)
        date_from = (start - timedelta(days=int(range) - 1)).isoformat()
    return render(
        request, "dashboard.html",
        active="dashboard",
        stats=queries.overview_stats(date_from, None),
        top=queries.top_performers(5),
        recent=queries.recent_calls(8),
        departments=queries.department_breakdown(),
        trend=queries.daily_trend(30),
        ranges=DASHBOARD_RANGES,
        current_range=range,
    )


@app.get("/top-performers", response_class=HTMLResponse)
async def top_performers_page(request: Request):
    return render(request, "top_performers.html", active="top", items=queries.top_performers(20))


@app.get("/ready-to-buy", response_class=HTMLResponse)
async def ready_to_buy_page(request: Request, page: int = 1, q: str = ""):
    page = max(page, 1)
    items = queries.ready_to_buy(20, (page - 1) * 20, q)
    return render(request, "ready_to_buy.html", active="ready", items=items, page=page, q=q)


@app.get("/unhappy-customers", response_class=HTMLResponse)
async def unhappy_page(request: Request, page: int = 1, q: str = ""):
    page = max(page, 1)
    items = queries.unhappy_customers(20, (page - 1) * 20, q)
    return render(request, "unhappy_customers.html", active="unhappy", items=items, page=page, q=q)


@app.get("/staff-performance", response_class=HTMLResponse)
async def staff_perf_page(request: Request):
    return render(request, "staff_performance.html", active="staff", items=queries.staff_performance())


@app.get("/call-duration", response_class=HTMLResponse)
async def call_duration_page(request: Request):
    return render(request, "call_duration.html", active="duration", items=queries.staff_call_duration())


@app.get("/satisfaction", response_class=HTMLResponse)
async def satisfaction_page(request: Request):
    return render(request, "satisfaction.html", active="satisfaction", items=queries.staff_satisfaction())


@app.get("/successful-sales", response_class=HTMLResponse)
async def sales_page(request: Request, page: int = 1, q: str = ""):
    page = max(page, 1)
    items = queries.successful_sales(20, (page - 1) * 20, q)
    return render(request, "successful_sales.html", active="sales", items=items, page=page, q=q)


@app.get("/monthly-reports", response_class=HTMLResponse)
async def monthly_page(request: Request):
    return render(request, "monthly_reports.html", active="monthly", items=queries.monthly_reports_list(24))


@app.get("/monthly-reports/{report_id}", response_class=HTMLResponse)
async def monthly_detail(request: Request, report_id: int):
    report = queries.monthly_report_detail(report_id)
    if not report:
        raise HTTPException(404)
    data = report.get("report_json") or {}
    if isinstance(data, str):
        data = json.loads(data)
    return render(request, "monthly_detail.html", active="monthly", report=report, data=data)


@app.get("/ai-insights", response_class=HTMLResponse)
async def ai_page(request: Request):
    return render(request, "ai_insights.html", active="ai")


@app.get("/api/ai-insights")
async def ai_insights_api():
    text = await generate_executive_insights(queries.ai_context_payload())
    return {"insights": text}


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str = ""):
    results = queries.search_calls(q, 50) if q else []
    return render(request, "search.html", active="search", results=results, q=q)


@app.get("/calls/{call_id}", response_class=HTMLResponse)
async def call_detail_page(request: Request, call_id: str):
    call = queries.call_detail(call_id)
    if not call:
        raise HTTPException(404)
    return render(
        request, "call_detail.html",
        active="calls", call=call, view=fmt.analysis_view(call.get("analysis_json")),
    )


# ── Upload ───────────────────────────────────────────────────────
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    require(request, "upload")
    return render(request, "upload.html", active="upload", max_mb=UPLOAD_MAX_MB)


async def _analyze_audio(content: bytes, filename: str, agent_name: str, customer_name: str,
                         department: str, call_id: str = "", customer_phone: str = "") -> dict:
    settings = brand()
    cid = call_id.strip() or f"web-{uuid.uuid4().hex[:12]}"
    try:
        transcript = await transcribe_audio(content, filename)
    except Exception as exc:
        log.exception("Transcription failed for %s", cid)
        raise HTTPException(502, f"رونویسی فایل صوتی انجام نشد: {exc}") from exc
    if not transcript or len(transcript) < 10:
        raise HTTPException(422, "در این فایل صدای قابل رونویسی پیدا نشد.")

    duration_sec = audio_duration_seconds(content, filename)
    call_date = datetime.now().astimezone().isoformat()
    meta = {
        "call_id": cid,
        "department": department or "auto",
        "agent_name": agent_name or "اپراتور",
        "customer_name": customer_name or "مشتری",
        "customer_phone": customer_phone,
        "call_direction": "inbound",
        "call_duration_seconds": duration_sec,
        "call_date": call_date,
    }
    try:
        analysis = await analyze_transcript(
            transcript,
            meta,
            product_context=settings.get("business_context", ""),
        )
    except Exception as exc:
        log.exception("Gemini analysis failed for %s", cid)
        raise HTTPException(502, f"تحلیل تماس انجام نشد: {exc}") from exc

    view = fmt.analysis_view(analysis)
    final_id = cid
    dept = (analysis.get("meta") or {}).get("department") or department or "auto"
    try:
        queries.upsert_call_analysis(
            call_id=final_id,
            department=dept,
            agent_name=agent_name or "اپراتور",
            customer_name=customer_name or "مشتری",
            customer_phone=customer_phone,
            call_date=call_date,
            call_direction="inbound",
            call_duration_seconds=duration_sec,
            transcript_text=transcript,
            analysis=analysis,
        )
    except Exception:
        log.exception("Failed to upsert call analysis for %s", final_id)

    notify_out = await _notify_after_call(final_id)
    log.info("Upload processed: %s (dept=%s)", final_id, dept)
    return {
        "success": True,
        "call_id": final_id,
        "department": dept,
        "department_label": fmt.label(dept, "department"),
        "email_sent": bool(notify_out.get("sent")),
        "sms_sent": bool(notify_out.get("sms_sent")),
        "customer_sms_sent": bool(notify_out.get("customer_sms_sent")),
        "transcript_length": len(transcript),
        "scores": {
            "purchase_intent": view["sales"]["intent"],
            "satisfaction": view["sat_final"],
            "agent_quality": view["agent"]["quality"],
        },
        "summary": view["summary"],
        "actions": view["actions"],
        "priority_label": fmt.label(view["ticket"]["priority"], "priority"),
        "panel_url": f"{PANEL_PUBLIC_URL}/calls/{final_id}",
    }


def _validate_audio(file: UploadFile, content: bytes):
    ext = Path(file.filename or "audio.mp3").suffix.lower()
    if ext not in AUDIO_EXTENSIONS:
        return f"فرمت {ext or 'نامشخص'} پشتیبانی نمی‌شود."
    if not content:
        return "فایل خالی است."
    if len(content) > UPLOAD_MAX_MB * 1024 * 1024:
        return f"حجم فایل بیش از {UPLOAD_MAX_MB} مگابایت است."
    return None


def _trusted_phone(request: Request, phone: str) -> str:
    """Anonymous demo uploads must not be able to trigger SMS to arbitrary numbers."""
    trusted = request.state.user or (API_TOKEN and request.headers.get("X-API-Token") == API_TOKEN)
    return phone.strip() if trusted else ""


def _upload_allowed(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if user and not auth.can(user, "upload"):
        raise HTTPException(403, "دسترسی آپلود ندارید.")
    if not _check_rate(f"upload:{_client_ip(request)}", RATE_LIMIT_RPM):
        raise HTTPException(429, "تعداد درخواست‌ها زیاد است. یک دقیقه دیگر تلاش کنید.")


@app.post("/api/upload-voice")
async def upload_voice(
    request: Request,
    file: UploadFile = File(...),
    agent_name: str = Form(""),
    customer_name: str = Form(""),
    department: str = Form("auto"),
    call_id: str = Form(""),
    customer_phone: str = Form(""),
):
    _upload_allowed(request)
    content = await file.read()
    error = _validate_audio(file, content)
    if error:
        raise HTTPException(400, error)
    result = await _analyze_audio(content, file.filename or "audio.mp3", agent_name, customer_name, department,
                                  call_id, _trusted_phone(request, customer_phone))
    return JSONResponse(result)


@app.post("/api/upload-batch")
async def upload_batch(
    request: Request,
    files: list[UploadFile] = File(...),
    agent_name: str = Form(""),
    customer_name: str = Form(""),
    department: str = Form("auto"),
    customer_phone: str = Form(""),
):
    _upload_allowed(request)
    customer_phone = _trusted_phone(request, customer_phone)
    if len(files) > 10:
        raise HTTPException(400, "حداکثر ۱۰ فایل در هر درخواست.")
    results = []
    for f in files:
        content = await f.read()
        error = _validate_audio(f, content)
        if error:
            results.append({"filename": f.filename, "success": False, "error": error})
            continue
        try:
            item = await _analyze_audio(content, f.filename or "audio.mp3", agent_name, customer_name, department,
                                        customer_phone=customer_phone)
            results.append({"filename": f.filename, **item})
        except HTTPException as exc:
            results.append({"filename": f.filename, "success": False, "error": exc.detail})
    succeeded = sum(1 for r in results if r.get("success"))
    return JSONResponse({"total": len(results), "succeeded": succeeded, "results": results})


# ── Settings (admin) ─────────────────────────────────────────────
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, saved: str = "", error: str = ""):
    require(request, "admin")
    return render(
        request, "settings.html",
        active="settings", settings=queries.get_settings(), rules=queries.list_alert_rules(),
        sms_log=sms.recent_log(15), saved=saved, error=error,
    )


@app.post("/settings")
async def settings_save(
    request: Request,
    company_name: str = Form(""),
    company_tagline: str = Form(""),
    business_context: str = Form(""),
    brand_color: str = Form("#4f46e5"),
    notify_emails: str = Form(""),
    notify_mode: str = Form("all"),
    remove_logo: str = Form(""),
    logo: UploadFile | None = File(None),
    sms_enabled: str = Form(""),
    sms_api_key: str = Form(""),
    sms_provider: str = Form("iransms"),
    sms_username: str = Form(""),
    sms_password: str = Form(""),
    sms_line_number: str = Form(""),
    sms_manager_numbers: str = Form(""),
    sms_manager_mode: str = Form("all"),
    sms_customer_enabled: str = Form(""),
    sms_customer_text: str = Form(""),
    gemini_api_key: str = Form(""),
):
    require(request, "admin")
    color = brand_color if brand_color.startswith("#") and len(brand_color) in (4, 7) else "#4f46e5"
    emails = ",".join(e.strip() for e in notify_emails.replace("،", ",").split(",") if e.strip())
    values = {
        "company_name": company_name.strip() or "اطلس",
        "company_tagline": company_tagline.strip(),
        "business_context": business_context.strip(),
        "brand_color": color,
        "notify_emails": emails,
        "notify_mode": notify_mode if notify_mode in ("all", "important", "off") else "all",
        "sms_enabled": "true" if sms_enabled == "on" else "false",
        "sms_provider": sms_provider if sms_provider in ("iransms", "ghasedaksms", "ghasedak_me") else "iransms",
        "sms_username": sms_username.strip(),
        "sms_line_number": ",".join(re.split(r"[,،;\s]+", sms_line_number.strip().translate(
            str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))).strip(","),
        "sms_manager_numbers": ",".join(sms.parse_numbers(sms_manager_numbers)),
        "sms_manager_mode": sms_manager_mode if sms_manager_mode in ("all", "important", "off") else "all",
        "sms_customer_enabled": "true" if sms_customer_enabled == "on" else "false",
        "sms_customer_text": sms_customer_text.strip().removesuffix(sms.OPT_OUT).strip(),
    }
    if sms_api_key.strip():
        values["sms_api_key"] = sms_api_key.strip()
    if sms_password:
        values["sms_password"] = sms_password
    if gemini_api_key.strip():
        values["gemini_api_key"] = gemini_api_key.strip()
    for key, value in values.items():
        queries.save_setting(key, value)
    if gemini_api_key.strip():
        from .ai_keys import invalidate_cache
        invalidate_cache()

    if remove_logo == "on":
        queries.save_setting("logo_data", "")
    elif logo is not None and logo.filename:
        data = await logo.read()
        if logo.content_type not in LOGO_TYPES or len(data) > 300 * 1024:
            _invalidate_brand()
            return RedirectResponse("/settings?error=logo", status_code=302)
        queries.save_setting("logo_data", f"data:{logo.content_type};base64,{base64.b64encode(data).decode()}")

    _invalidate_brand()
    return RedirectResponse("/settings?saved=1", status_code=302)


@app.post("/settings/rule")
async def rule_save(
    request: Request,
    rule_id: str = Form(""),
    name: str = Form(...),
    rule_type: str = Form(...),
    threshold: int = Form(5),
    time_window_minutes: int = Form(60),
    email_to: str = Form(""),
    enabled: str = Form("off"),
):
    require(request, "admin")
    queries.save_alert_rule(
        int(rule_id) if rule_id else None,
        name, rule_type, threshold, time_window_minutes, enabled == "on", email_to,
    )
    return RedirectResponse("/settings?saved=rule#rules", status_code=302)


@app.post("/settings/rule/{rule_id}/delete")
async def rule_delete(request: Request, rule_id: int):
    require(request, "admin")
    queries.delete_alert_rule(rule_id)
    return RedirectResponse("/settings#rules", status_code=302)


@app.post("/settings/rule/{rule_id}/toggle")
async def rule_toggle(request: Request, rule_id: int):
    require(request, "admin")
    current = next((r for r in queries.list_alert_rules() if r["id"] == rule_id), None)
    if current:
        queries.toggle_alert_rule(rule_id, not current["enabled"])
    return RedirectResponse("/settings#rules", status_code=302)


@app.get("/api/check-alerts")
async def check_alerts_api(request: Request):
    require(request, "admin")
    triggered = queries.check_alerts()
    settings = queries.get_settings()
    company = settings.get("company_name") or "اطلس"
    sent = 0
    for alert in triggered:
        to = alert.get("email_to") or settings.get("notify_emails", "")
        if not to:
            continue
        result = await notify.send_mail(to, f"{company} | {alert['subject']}", alert["body"], from_name=company)
        if result.get("success"):
            sent += 1
    sms_sent = 0
    if triggered and notify.sms_ready(settings):
        text = sms.fit([f"{company} | {len(triggered)} هشدار جدید"] + [a["subject"] for a in triggered[:3]],
                       notify.MANAGER_SMS_LIMIT)
        sms_sent = sum(1 for r in await notify.sms_managers(settings, text, "alert") if r.get("success"))
    return {"triggered": len(triggered), "sent": sent, "sms_sent": sms_sent, "alerts": triggered}


@app.post("/api/test-email")
async def test_email_api(request: Request):
    require(request, "admin")
    settings = queries.get_settings()
    to = settings.get("notify_emails", "")
    if not to:
        raise HTTPException(400, "ابتدا ایمیل گیرنده را در تنظیمات ذخیره کنید.")
    company = settings.get("company_name") or "اطلس"
    latest = queries.recent_calls(1)
    call = queries.call_detail(latest[0]["call_id"]) if latest else None
    if call:
        subject, html, text = notify.build_email(call, settings, templates)
        subject = f"[آزمایشی] {subject}"
    else:
        subject = f"{company} | ایمیل آزمایشی پنل تحلیل تماس"
        text = "این یک ایمیل آزمایشی است. اگر آن را دریافت کرده‌اید، ارسال گزارش تحلیل تماس به درستی تنظیم شده است."
        html = ""
    data = await notify.send_mail(to, subject, text, html, from_name=company)
    if not data.get("success"):
        raise HTTPException(502, "ارسال ایمیل ناموفق بود. تنظیمات SMTP سرور را بررسی کنید.")
    return {"sent_to": to}


async def _notify_after_call(call_id: str, to_override: str = "") -> dict:
    call = queries.call_detail(call_id)
    if not call:
        return {"sent": False, "skipped": "call_not_found"}
    settings = queries.get_settings()
    to = to_override or settings.get("notify_emails", "")
    mode = settings.get("notify_mode", "all")
    out: dict = {"sent": False}
    if not to:
        out["skipped"] = "no_recipients"
    elif mode == "off" or (mode == "important" and not notify.is_important(call)):
        out["skipped"] = f"mode_{mode}"
    else:
        subject, html, text = notify.build_email(call, settings, templates)
        result = await notify.send_mail(to, subject, text, html, from_name=settings.get("company_name", ""))
        if not result.get("success"):
            log.error("Notify email failed for %s: %s", call["call_id"], result.get("error"))
        out.update(sent=bool(result.get("success")), to=to, error=result.get("error"))
    out["sms"] = await notify.send_call_sms(call, settings)
    managers = out["sms"].get("manager")
    out["sms_sent"] = isinstance(managers, list) and any(r.get("success") for r in managers)
    customer = out["sms"].get("customer")
    out["customer_sms_sent"] = isinstance(customer, dict) and bool(customer.get("success"))
    return out


@app.post("/api/notify-call")
async def notify_call_api(request: Request):
    """Called by the n8n workflow after a call is saved; emails managers per notify settings."""
    body = await request.json()
    return await _notify_after_call(str(body.get("call_id", "")), to_override=body.get("to") or "")


@app.post("/api/test-sms")
async def test_sms_api(request: Request):
    require(request, "admin")
    settings = queries.get_settings()
    if not sms.configured(settings):
        raise HTTPException(400, "ابتدا اطلاعات اتصال سامانه پیامک را در تنظیمات ذخیره کنید.")
    if not sms.parse_numbers(settings.get("sms_manager_numbers", "")):
        raise HTTPException(400, "ابتدا شماره موبایل مدیر را در تنظیمات ذخیره کنید.")
    latest = queries.recent_calls(1)
    call = queries.call_detail(latest[0]["call_id"]) if latest else None
    if call:
        text = notify.build_manager_sms(call, settings)
    else:
        text = f"{settings.get('company_name') or 'اطلس'} | پیامک آزمایشی پنل تحلیل تماس"
    results = await notify.sms_managers(settings, text, "test")
    if not any(r.get("success") for r in results):
        raise HTTPException(502, results[0].get("error") if results else "ارسال پیامک ناموفق بود.")
    return {"sent_to": [r["receptor"] for r in results if r.get("success")], "text": sms.with_opt_out(text)}


@app.get("/api/sms-credit")
async def sms_credit_api(request: Request):
    require(request, "admin")
    return await sms.account_info(queries.get_settings())


# ── Users (admin) & account ──────────────────────────────────────
@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, msg: str = ""):
    require(request, "admin")
    return render(request, "users.html", active="users", users=auth.list_users(), msg=msg)


@app.post("/users")
async def users_create(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(""),
    password: str = Form(...),
    role: str = Form("viewer"),
):
    require(request, "admin")
    if role not in auth.ROLES or len(password) < 8 or not username.strip():
        return RedirectResponse("/users?msg=invalid", status_code=302)
    try:
        auth.create_user(username, full_name, password, role)
    except Exception:
        return RedirectResponse("/users?msg=exists", status_code=302)
    return RedirectResponse("/users?msg=created", status_code=302)


@app.post("/users/{user_id}/toggle")
async def users_toggle(request: Request, user_id: int):
    require(request, "admin")
    target = auth.get_user(user_id)
    if target and target["id"] != request.state.user["id"]:
        auth.set_active(user_id, not target["is_active"])
    return RedirectResponse("/users", status_code=302)


@app.post("/users/{user_id}/password")
async def users_reset_password(request: Request, user_id: int, password: str = Form(...)):
    require(request, "admin")
    if len(password) < 8:
        return RedirectResponse("/users?msg=invalid", status_code=302)
    auth.set_password(user_id, password)
    return RedirectResponse("/users?msg=password", status_code=302)


@app.post("/users/{user_id}/delete")
async def users_delete(request: Request, user_id: int):
    require(request, "admin")
    if user_id != request.state.user["id"]:
        auth.delete_user(user_id)
    return RedirectResponse("/users?msg=deleted", status_code=302)


@app.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, msg: str = ""):
    return render(request, "account.html", active="account", msg=msg)


@app.post("/account/password")
async def account_password(
    request: Request,
    current: str = Form(...),
    password: str = Form(...),
    confirm: str = Form(...),
):
    user = request.state.user
    if not auth.verify_password(current, user["password_hash"]):
        return RedirectResponse("/account?msg=wrong", status_code=302)
    if len(password) < 8 or password != confirm:
        return RedirectResponse("/account?msg=invalid", status_code=302)
    auth.set_password(user["id"], password)
    refreshed = auth.get_user(user["id"])
    token, max_age = auth.make_session(refreshed, remember=True)
    resp = RedirectResponse("/account?msg=ok", status_code=302)
    resp.set_cookie(auth.COOKIE_NAME, token, max_age=max_age, httponly=True, samesite="lax",
                    secure=request.headers.get("x-forwarded-proto") == "https")
    return resp


# ── CSV export ───────────────────────────────────────────────────
def _csv_value(v):
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


@app.get("/export/{report_type}")
async def export_csv(report_type: str):
    exporters = {
        "recent": ("recent_calls.csv", lambda: queries.recent_calls(500)),
        "top-performers": ("top_performers.csv", lambda: queries.top_performers(50)),
        "ready-to-buy": ("ready_to_buy.csv", lambda: queries.ready_to_buy(200)),
        "unhappy": ("unhappy_customers.csv", lambda: queries.unhappy_customers(200)),
        "staff": ("staff_performance.csv", queries.staff_performance),
        "duration": ("call_duration.csv", queries.staff_call_duration),
        "satisfaction": ("satisfaction.csv", queries.staff_satisfaction),
        "sales": ("successful_sales.csv", lambda: queries.successful_sales(200)),
    }
    if report_type not in exporters:
        raise HTTPException(404)
    filename, loader = exporters[report_type]
    rows = loader()
    if not rows:
        raise HTTPException(404)
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _csv_value(v) for k, v in row.items()})
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── JSON API ─────────────────────────────────────────────────────
@app.get("/api/stats")
async def api_stats():
    return JSONResponse(jsonable_encoder(queries.overview_stats()), headers={"Cache-Control": "no-store"})


@app.get("/api/recent-calls")
async def api_recent_calls(request: Request, limit: int = 10):
    rows = queries.recent_calls(max(1, min(limit, 100)))
    if not request.state.user:
        for r in rows:
            name = r.get("customer_name") or ""
            r["customer_name"] = (name[:1] + "•••") if name else ""
    return JSONResponse(jsonable_encoder(rows), headers={"Cache-Control": "no-store"})


@app.get("/api/trend")
async def api_trend(days: int = 30):
    return queries.daily_trend(max(1, min(days, 365)))


@app.get("/api/departments")
async def api_departments():
    return queries.department_breakdown()


@app.get("/api/top-performers")
async def api_top_performers(limit: int = 10):
    return queries.top_performers(max(1, min(limit, 50)))


@app.get("/api/health")
async def health_check():
    from .ai_keys import gemini_api_key

    try:
        queries.overview_stats()
        db = "ok"
    except Exception:
        db = "error"
    return JSONResponse(
        {
            "status": "ok" if db == "ok" else "degraded",
            "database": db,
            "gemini_configured": bool(gemini_api_key()),
            "timestamp": datetime.now().isoformat(),
        },
        status_code=200 if db == "ok" else 503,
    )
