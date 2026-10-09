"""Lightweight audio duration helpers (no ffmpeg dependency)."""
import io
import wave


def audio_duration_seconds(content: bytes, filename: str) -> int:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
    if ext == "wav":
        try:
            with wave.open(io.BytesIO(content), "rb") as handle:
                rate = handle.getframerate() or 1
                return max(1, int(handle.getnframes() / rate))
        except Exception:
            pass
    size = len(content)
    if size < 1:
        return 0
    # Heuristic bitrates for compressed voice recordings.
    bitrate = {
        "mp3": 128_000,
        "m4a": 96_000,
        "mp4": 96_000,
        "aac": 96_000,
        "ogg": 96_000,
        "webm": 96_000,
        "flac": 256_000,
    }.get(ext, 96_000)
    return max(1, int(size * 8 / bitrate))
