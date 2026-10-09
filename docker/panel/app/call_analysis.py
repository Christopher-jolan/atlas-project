"""Full call analysis via Gemini (same path as transcription — avoids n8n/llm fallback)."""
import json
import logging
import re
from datetime import datetime, timezone

from .ai_keys import gemini_api_key
from .gemini import gemini_text

log = logging.getLogger("atlas.call_analysis")

_SCHEMA_HINT = {
    "executive_summary": "",
    "sms_brief": "",
    "next_actions": [],
    "meta": {"department": "sales|support|mixed|unknown", "confidence_overall": 0},
    "customer": {
        "request_summary": "",
        "needs": [],
        "pain_points": [],
        "products_mentioned": [],
        "sentiment": {"overall": "positive|neutral|negative|mixed", "score": 0},
        "satisfaction": {"initial_score": 0, "final_score": 0, "resolved": None},
    },
    "agent_performance": {
        "response_quality_score": 0,
        "communication_skills": 0,
        "product_knowledge": 0,
        "empathy_score": 0,
        "process_adherence": 0,
        "strengths": [],
        "improvements": [],
    },
    "sales_analysis": {
        "applicable": False,
        "purchase_intent_score": 0,
        "purchase_stage": "awareness|interest|consideration|evaluation|negotiation|decision|purchase|closed_won|closed_lost",
        "main_objections": [],
        "price_sensitivity": "low|medium|high",
        "estimated_discount_to_close_percent": None,
        "estimated_close_probability_percent": 0,
        "recommended_next_step": "",
        "competitor_mentions": [],
    },
    "support_analysis": {
        "applicable": False,
        "issue_category": "",
        "issue_summary": "",
        "resolution_status": "resolved|partial|unresolved|escalated",
        "first_call_resolution": None,
        "customer_retention_risk": "low|medium|high",
    },
    "ticket": {
        "title": "",
        "priority": "low|medium|high|urgent",
        "description": "",
        "actionable": True,
        "recommended_assignee": "",
        "follow_up_required": False,
        "follow_up_date": "YYYY-MM-DD or empty",
        "tags": [],
    },
    "insights": {"key_takeaways": [], "risks": [], "opportunities": [], "compliance_notes": []},
    "quality_control": {
        "transcript_quality": "good|fair|poor",
        "needs_human_review": False,
        "review_reason": "",
    },
}


def _norm_score(obj: dict | None, key: str) -> None:
    if not obj or not isinstance(obj.get(key), (int, float)):
        return
    v = obj[key]
    if 0 < v <= 1:
        v *= 100
    obj[key] = max(0, min(100, round(v)))


def _normalize(analysis: dict, meta: dict) -> dict:
    sa = analysis.get("sales_analysis") or {}
    ca = analysis.get("customer") or {}
    sat = ca.get("satisfaction") or {}
    ap = analysis.get("agent_performance") or {}
    for k in (
        "purchase_intent_score",
        "estimated_close_probability_percent",
    ):
        _norm_score(sa, k)
    for k in ("initial_score", "final_score"):
        _norm_score(sat, k)
    for k in (
        "response_quality_score",
        "communication_skills",
        "product_knowledge",
        "empathy_score",
        "process_adherence",
    ):
        _norm_score(ap, k)
    analysis.setdefault("meta", {})
    _norm_score(analysis["meta"], "confidence_overall")
    dept = (meta.get("department") or "").lower()
    if dept in ("sales", "support"):
        analysis["meta"]["department"] = dept
    if analysis["meta"].get("department") not in ("sales", "support", "mixed", "unknown"):
        analysis["meta"]["department"] = "unknown"
    if not isinstance(analysis.get("next_actions"), list):
        na = analysis.get("next_actions")
        analysis["next_actions"] = [str(na)] if na else []
    return analysis


def _build_prompt(transcript: str, meta: dict, product_context: str) -> str:
    dept = (meta.get("department") or "auto").lower()
    if dept == "sales":
        dept_hint = "This is a SALES call."
    elif dept == "support":
        dept_hint = "This is a SUPPORT call."
    else:
        dept_hint = "Detect the department yourself."
    today = datetime.now(timezone.utc).astimezone().date().isoformat()
    return f"""You are a senior sales and customer-experience analyst writing for the managers of the company whose staff answered this call.
Business context (use it to make every recommendation specific to this business; take company and product names from the transcript): {product_context or "not provided"}
{dept_hint}
Call metadata: agent={meta.get("agent_name") or "unknown"}, customer={meta.get("customer_name") or meta.get("customer_phone") or "unknown"}, date={meta.get("call_date")}, today={today}

Analyze the call transcript below and return ONLY one valid JSON object (no markdown) with exactly this structure:
{json.dumps(_SCHEMA_HINT, ensure_ascii=False)}

Writing rules:
- Every text value must be fluent, natural, polite Persian (Farsi) that a busy manager can read in seconds. Keys stay in English. Enum fields use one of the listed English values.
- executive_summary: 2 to 4 sentences — who called, what they wanted, what happened, and the single most important point for the manager.
- sms_brief: the single most important action for the manager in at most 45 Persian characters, no links, no emoji.
- next_actions: 1 to 5 concrete, imperative actions in Persian.
- All scores and percentages are integers from 0 to 100.
- Use only facts from the transcript. Do not invent prices, names or dates.
- quality_control.needs_human_review=true when the customer is angry, there is legal/financial risk, a big deal is at stake, or the transcript is unclear.

Transcript:
{transcript}"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.I)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_balanced_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("no JSON object", text, 0)
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    # Truncated — return best effort and let repair close brackets
    return text[start:]


def _repair_json_text(text: str) -> str:
    text = _strip_fences(text)
    text = text.replace("\ufeff", "").replace("“", '"').replace("”", '"').replace("„", '"')
    text = _extract_balanced_object(text)
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    # Remove // and /* */ comments (invalid in JSON but models sometimes add them)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    return text


def _parse_json(text: str) -> dict:
    candidates = [
        text,
        _repair_json_text(text),
    ]
    m = re.search(r"\{[\s\S]*\}", _strip_fences(text))
    if m:
        candidates.append(_repair_json_text(m.group(0)))
    last_err: json.JSONDecodeError | None = None
    for cand in candidates:
        try:
            return json.loads(cand)
        except json.JSONDecodeError as exc:
            last_err = exc
            # Close missing brackets if output was cut off
            if cand.count("{") > cand.count("}"):
                padded = cand + ("}" * (cand.count("{") - cand.count("}")))
                padded = re.sub(r",\s*}", "}", padded)
                try:
                    return json.loads(padded)
                except json.JSONDecodeError as exc2:
                    last_err = exc2
    assert last_err is not None
    raise last_err


async def _repair_json_via_gemini(broken: str) -> dict:
    snippet = broken[:14000]
    prompt = (
        "The text below must become ONE valid JSON object. "
        "Fix syntax only (quotes, commas, brackets). Keep all Persian text and keys unchanged. "
        "Output ONLY JSON, no markdown.\n\n"
        f"{snippet}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 32768,
            "responseMimeType": "application/json",
        },
    }
    fixed = await gemini_text(payload, timeout=300, prefer=["gemini-3.5-flash-lite", "gemini-2.5-flash"], min_len=20)
    return _parse_json(fixed)


async def analyze_transcript(
    transcript: str,
    meta: dict,
    product_context: str = "",
) -> dict:
    if not gemini_api_key():
        raise RuntimeError("کلید Gemini تنظیم نشده (AI_API_KEY یا تنظیمات پنل).")
    prompt = _build_prompt(transcript, meta, product_context)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 32768,
            "responseMimeType": "application/json",
        },
    }
    raw = await gemini_text(
        payload, timeout=600,
        prefer=["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-flash-latest"],
        min_len=20,
    )
    try:
        analysis = _parse_json(raw)
    except json.JSONDecodeError as exc:
        log.warning("analysis JSON parse failed (%s), attempting repair", exc)
        try:
            analysis = await _repair_json_via_gemini(raw)
        except Exception as repair_exc:
            log.exception("JSON repair failed")
            raise RuntimeError(f"پاسخ تحلیل قابل خواندن نبود: {exc}") from repair_exc
    analysis = _normalize(analysis, meta)
    analysis["meta"].update({
        "call_id": meta.get("call_id"),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "workflow_version": "panel-2.1",
        "language": "fa",
        "call_date": meta.get("call_date"),
        "call_direction": meta.get("call_direction", "inbound"),
        "call_duration_seconds": meta.get("call_duration_seconds") or 0,
    })
    analysis["transcript"] = {"full_text": transcript}
    analysis["input"] = {
        "agent_id": meta.get("agent_id", ""),
        "agent_name": meta.get("agent_name", ""),
        "customer_phone": meta.get("customer_phone", ""),
        "customer_name": meta.get("customer_name", ""),
    }
    if analysis.get("quality_control", {}).get("analysis_flags"):
        qc = analysis["quality_control"]
        flags = [f for f in qc["analysis_flags"] if f != "gemini_unavailable"]
        qc["analysis_flags"] = flags
    return analysis
