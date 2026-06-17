import time
import httpx
from app.config import settings


def transcribe_with_sarvam(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    start = time.time()
    headers = {"api-subscription-key": settings.SARVAM_API_KEY}
    files = {"file": (filename, audio_bytes, "audio/webm")}
    data = {
        "model": "saarika:v2",
        "language_code": "unknown",
        "with_timestamps": "false",
    }
    response = httpx.post(
        "https://api.sarvam.ai/speech-to-text",
        headers=headers,
        files=files,
        data=data,
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()
    return {
        "text": result.get("transcript", ""),
        "language": result.get("language_code", "unknown"),
        "provider": "sarvam",
        "model": "saarika:v2",
        "processing_time_ms": int((time.time() - start) * 1000),
    }


def transcribe_with_whisper(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    start = time.time()
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=(filename, audio_bytes, "audio/webm"),
    )
    return {
        "text": response.text,
        "language": "auto",
        "provider": "whisper",
        "model": "whisper-1",
        "processing_time_ms": int((time.time() - start) * 1000),
    }


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Try Sarvam first (better Hinglish), fall back to Whisper."""
    if settings.SARVAM_API_KEY:
        try:
            return transcribe_with_sarvam(audio_bytes, filename)
        except Exception as e:
            if not settings.OPENAI_API_KEY:
                raise
    return transcribe_with_whisper(audio_bytes, filename)
