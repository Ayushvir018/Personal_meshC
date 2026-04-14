"""
voice_engine.py — Edge-TTS Voice Output Engine for Personal Mesh
Generates high-quality Hindi-English speech using Microsoft Edge TTS.
Uses st.audio(autoplay=True) for reliable cross-browser playback.
"""

import asyncio
import edge_tts
import tempfile
import os
from pathlib import Path

# ── TTS Config ────────────────────────────────────────────────────────────────
VOICE = "en-IN-NeerjaNeural"   # Natural Indian English female voice
RATE  = "+10%"                  # Slightly faster — sounds sharper
PITCH = "+0Hz"


def _clean_text(text: str) -> str:
    """Strip markdown/emoji symbols unsuitable for TTS."""
    clean = (
        text.replace("**", "").replace("*", "").replace("`", "")
            .replace("#", "").replace("🐾", "").replace("⬡", "")
            .replace("→", " ").replace("•", " ").replace("—", " ")
    )
    # Truncate to avoid very long TTS (max ~500 chars ≈ ~40s audio)
    return clean[:500].strip()


async def _async_tts(text: str, voice: str, rate: str, pitch: str, path: str):
    """Internal async TTS generation."""
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(path)


def text_to_speech_bytes(
    text: str,
    voice: str = VOICE,
    rate: str  = RATE,
    pitch: str = PITCH
) -> bytes | None:
    """
    Convert text to speech using edge-tts.
    Returns raw MP3 bytes, or None on failure.
    Use with Streamlit: st.audio(bytes, format='audio/mp3', autoplay=True)
    """
    clean = _clean_text(text)
    if not clean:
        return None

    tmp_path = None
    try:
        tmp_path = tempfile.mktemp(suffix=".mp3")
        asyncio.run(_async_tts(clean, voice, rate, pitch, tmp_path))
        return Path(tmp_path).read_bytes()
    except Exception as e:
        print(f"[voice_engine] TTS failed: {e}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def estimate_duration(text: str, rate_pct: int = 10) -> float:
    """Rough estimate of TTS duration in seconds (~150 WPM baseline)."""
    words = len(text.split())
    wpm = 150 * (1 + rate_pct / 100)
    return max(1.0, (words / wpm) * 60)
