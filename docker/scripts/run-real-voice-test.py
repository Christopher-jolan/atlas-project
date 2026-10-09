#!/usr/bin/env python3
"""Transcribe audio with Gemini and run Atlas Call Intelligence via n8n."""
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

API_KEY = os.getenv("AI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
N8N_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/atlas/call-intelligence")


def transcribe(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    mime = "audio/mp4" if path.suffix.lower() in {".m4a", ".mp4"} else "audio/mpeg"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": mime, "data": data}},
                {"text": (
                    "این یک تماس تلفنی فارسی بین اپراتور شرکت و مشتری است. "
                    "کل مکالمه را کلمه به کلمه و دقیق رونویسی کن. "
                    "هر جمله را با برچسب «اپراتور:» یا «مشتری:» مشخص کن. "
                    "فقط متن رونوشت را برگردان، بدون توضیح اضافه."
                )},
            ]
        }],
        "generationConfig": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        GEMINI_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    parts = result["candidates"][0]["content"]["parts"]
    return "\n".join(p.get("text", "") for p in parts).strip()


def analyze(transcript: str, call_id: str) -> dict:
    body = {
        "call_id": call_id,
        "department": "auto",
        "transcript": transcript,
        "agent_name": "شرکت آتیران",
        "customer_name": "مشتری (تماس واقعی)",
        "call_direction": "inbound",
        "product_context": "شرکت آتیران - نرم‌افزار حسابداری و خدمات مالی",
    }
    req = urllib.request.Request(
        N8N_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    audio = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"F:\atlas project\docker\n8n\data\a test coversation\Call recording Sherkat Atiran_260715_155444.m4a"
    )
    if not audio.exists():
        print(f"ERROR: file not found: {audio}")
        return 1

    call_id = "atiran-real-call-001"
    print(f"Transcribing: {audio.name} ({audio.stat().st_size / 1024 / 1024:.1f} MB)...")
    transcript = transcribe(audio)
    print(f"Transcript length: {len(transcript)} chars")
    Path(r"F:\atlas project\docker\scripts\real-call-transcript.txt").write_text(transcript, encoding="utf-8")

    print("Sending to n8n for analysis + email...")
    result = analyze(transcript, call_id)
    out = Path(r"F:\atlas project\docker\scripts\real-call-result.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"success={result.get('success')} department={result.get('department')} email_sent={result.get('email_sent')}")
    return 0 if result.get("email_sent") else 1


if __name__ == "__main__":
    raise SystemExit(main())
