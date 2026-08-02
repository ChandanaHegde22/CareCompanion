"""
speech/tts.py – Text-to-Speech using gTTS (online) with pyttsx3 fallback.
Returns audio bytes playable in Streamlit via st.audio().
"""

import logging
from io import BytesIO

logger = logging.getLogger(__name__)

LANG_TTS = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
}

_gtts_available   = False
_pyttsx3_available = False

try:
    from gtts import gTTS
    _gtts_available = True
except ImportError:
    logger.warning("gTTS not available.")

try:
    import pyttsx3
    _pyttsx3_available = True
except ImportError:
    logger.warning("pyttsx3 not available.")


def text_to_speech_bytes(text: str, language: str = "en",
                          slow: bool = False) -> bytes | None:
    """
    Convert *text* to MP3 audio bytes using gTTS.
    Returns raw bytes or None on failure.
    """
    if not text.strip():
        return None
    lang_code = LANG_TTS.get(language, "en")

    if _gtts_available:
        try:
            tts    = gTTS(text=text[:3000], lang=lang_code, slow=slow)
            buffer = BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            return buffer.read()
        except Exception as exc:
            logger.warning("gTTS failed: %s", exc)

    logger.error("No TTS backend available.")
    return None


def speak_in_streamlit(text: str, language: str = "en") -> None:
    """
    Play TTS audio inline in a Streamlit app.
    Renders st.audio() with the generated MP3.
    """
    import streamlit as st
    audio_bytes = text_to_speech_bytes(text, language)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
    else:
        st.warning("🔇 Text-to-speech is currently unavailable. Please check your internet connection.")
