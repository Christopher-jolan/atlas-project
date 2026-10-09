import base64

import httpx

from .config import AI_API_KEY, TRANSCRIPTION_API_URL
from .gemini import gemini_text


async def transcribe_audio(content: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
    mime_map = {
        "m4a": "audio/mp4", "mp4": "audio/mp4", "mp3": "audio/mpeg",
        "wav": "audio/wav", "ogg": "audio/ogg", "webm": "audio/webm",
        "aac": "audio/aac", "flac": "audio/flac",
    }
    mime = mime_map.get(ext, "audio/mpeg")

    if AI_API_KEY:
        return await _transcribe_gemini(content, mime)
    return await _transcribe_ollama(content, filename)


async def _transcribe_gemini(content: bytes, mime: str) -> str:
    data = base64.b64encode(content).decode("ascii")
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
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 32768},
    }
    return await gemini_text(
        payload, timeout=600, prefer=["gemini-2.5-flash"], min_len=10,
    )


async def _transcribe_ollama(content: bytes, filename: str) -> str:
    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            TRANSCRIPTION_API_URL,
            files={"file": (filename, content)},
            data={"model": "whisper"},
        )
        resp.raise_for_status()
        data = resp.json()
    return (data.get("text") or data.get("transcript") or "").strip()
