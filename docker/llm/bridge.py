#!/usr/bin/env python3
"""OpenAI-compatible Gemini bridge for n8n + panel transcription."""
from __future__ import annotations

import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import urllib.error
import urllib.request

API_KEY = os.getenv("AI_API_KEY", "").strip()
DEFAULT_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash").strip()
PORT = int(os.getenv("LLM_PORT", "8080"))
GEMINI_MODELS = [
    DEFAULT_MODEL,
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-2.5-flash-lite",
]


def _unique(seq):
    seen = set()
    out = []
    for x in seq:
        if x and x not in seen and ":" not in x:
            seen.add(x)
            out.append(x)
        elif x and ":" in x:
            continue
    return out or ["gemini-2.5-flash"]


MODELS = _unique(GEMINI_MODELS)


def gemini_generate(
    prompt: str, model: str | None = None, timeout: int = 300, json_mode: bool = False,
) -> str:
    if not API_KEY:
        raise RuntimeError("AI_API_KEY is empty")
    last_err = None
    models = _unique([model] + MODELS) if model else MODELS
    generation = {"temperature": 0.1, "maxOutputTokens": 32768}
    if json_mode:
        generation["responseMimeType"] = "application/json"
    for m in models:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
            f"?key={API_KEY}"
        )
        payload = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                parts = data["candidates"][0]["content"]["parts"]
                text = "\n".join(p.get("text", "") for p in parts).strip()
                if text:
                    print("gemini ok", m, "attempt", attempt)
                    return text
                last_err = RuntimeError(f"{m}: empty text {str(data)[:200]}")
                break
            except urllib.error.HTTPError as exc:
                body = exc.read()[:300]
                print("gemini fail", m, exc.code, body)
                last_err = exc
                if exc.code in (429, 503) and attempt < 3:
                    time.sleep(2 ** attempt)
                    continue
                break
            except Exception as exc:
                print("gemini fail", m, exc)
                last_err = exc
                break
    raise RuntimeError(f"Gemini failed: {last_err}")


def openai_chat_response(text: str, model: str) -> dict:
    return {
        "id": "atlas-gemini",
        "object": "chat.completion",
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop",
        }],
    }


def json_fallback(prompt: str) -> str:
    """Last-resort structured JSON so the pipeline still stores a row."""
    t = prompt
    m = re.search(r"Transcript:\n(.+)$", prompt, re.S)
    transcript = (m.group(1) if m else prompt)[-4000:]
    sales = any(w in transcript for w in ("خرید", "قیمت", "فاکتور", "سفارش", "تخفیف"))
    unhappy = any(w in transcript for w in ("ناراضی", "شکایت", "عودت", "خراب"))
    return json.dumps({
        "meta": {
            "department": "sales" if sales else "support",
            "language": "fa",
            "workflow_version": "1.0.0",
            "confidence_overall": 40,
        },
        "transcript": {"full_text": transcript, "segments": [], "word_count": len(transcript.split())},
        "customer": {
            "request_summary": transcript[:240],
            "needs": [],
            "pain_points": [],
            "products_mentioned": [],
            "sentiment": {"overall": "negative" if unhappy else "neutral", "score": 35 if unhappy else 55},
            "satisfaction": {
                "initial_score": 40,
                "final_score": 35 if unhappy else 60,
                "delta": 0,
                "resolved": None,
            },
        },
        "agent_performance": {
            "name": "",
            "response_quality_score": 55,
            "communication_skills": 55,
            "product_knowledge": 50,
            "empathy_score": 50,
            "process_adherence": 50,
            "strengths": [],
            "improvements": ["بررسی انسانی — مدل Gemini در دسترس نبود"],
            "key_actions_taken": [],
        },
        "sales_analysis": {
            "applicable": sales,
            "purchase_intent_score": 60 if sales else 20,
            "purchase_stage": "consideration" if sales else "",
            "main_objections": [],
            "price_sensitivity": "medium",
            "estimated_discount_to_close_percent": None,
            "estimated_close_probability_percent": 40 if sales else 0,
            "recommended_next_step": "پیگیری تلفنی",
            "competitor_mentions": [],
        },
        "support_analysis": {
            "applicable": not sales,
            "issue_category": "general",
            "issue_summary": transcript[:180],
            "resolution_status": "unresolved",
            "first_call_resolution": None,
            "process_management_score": 50,
            "customer_retention_risk": "high" if unhappy else "low",
        },
        "ticket": {
            "title": "تحلیل تماس (fallback)",
            "priority": "high" if unhappy else "medium",
            "category": "sales" if sales else "support",
            "description": transcript[:500],
            "actionable": True,
            "recommended_assignee": "",
            "follow_up_required": True,
            "follow_up_date": "",
            "tags": ["fallback"],
        },
        "insights": {
            "key_takeaways": ["تحلیل با مدل اضطراری محلی انجام شد"],
            "risks": [],
            "opportunities": [],
            "compliance_notes": [],
        },
        "quality_control": {
            "transcript_quality": "unknown",
            "analysis_flags": ["gemini_unavailable"],
            "needs_human_review": True,
            "review_reason": "Gemini API failed; fallback analyzer used",
        },
    }, ensure_ascii=False)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path in ("/health", "/v1/models"):
            self._send(200, {"status": "ok", "has_key": bool(API_KEY), "models": MODELS})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return

        if self.path.rstrip("/") in ("/v1/chat/completions", "/chat/completions"):
            msgs = data.get("messages") or []
            prompt = "\n".join(m.get("content", "") for m in msgs if m.get("content"))
            model = data.get("model") or DEFAULT_MODEL
            try:
                json_mode = (data.get("response_format") or {}).get("type") == "json_object"
                text = gemini_generate(prompt, model, json_mode=json_mode)
            except Exception as exc:
                print("gemini error:", exc)
                text = json_fallback(prompt)
            self._send(200, openai_chat_response(text, MODELS[0]))
            return

        self._send(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(fmt % args)


if __name__ == "__main__":
    print(f"Atlas LLM bridge on :{PORT} key={bool(API_KEY)} models={MODELS}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
