"""
speech/stt.py – Speech-to-Text using SpeechRecognition.
Works with the audio_recorder_streamlit widget in the browser.
"""

import logging
from io import BytesIO

logger = logging.getLogger(__name__)

_sr_available = False
try:
    import speech_recognition as sr
    _sr_available = True
except ImportError:
    logger.warning("SpeechRecognition not installed.")

LANG_SR = {
    "en": "en-US",
    "hi": "hi-IN",
    "kn": "kn-IN",
}


def audio_bytes_to_text(audio_bytes: bytes, language: str = "en") -> dict:
    """
    Convert raw WAV/audio bytes (from audio_recorder_streamlit) to text.

    Returns::

        {"success": bool, "text": str, "error": str}
    """
    if not _sr_available:
        return {"success": False, "text": "",
                "error": "SpeechRecognition library not installed."}

    if not audio_bytes:
        return {"success": False, "text": "", "error": "No audio received."}

    lang_code = LANG_SR.get(language, "en-US")
    recognizer = sr.Recognizer()

    try:
        audio_file = BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data, language=lang_code)
        logger.info("STT recognised: '%s'", text[:80])
        return {"success": True, "text": text, "error": ""}

    except sr.UnknownValueError:
        return {"success": False, "text": "",
                "error": "Could not understand the audio. Please speak clearly."}
    except sr.RequestError as exc:
        return {"success": False, "text": "",
                "error": f"Speech service error: {exc}"}
    except Exception as exc:
        logger.error("STT error: %s", exc, exc_info=True)
        return {"success": False, "text": "", "error": str(exc)}


def is_stt_available() -> bool:
    return _sr_available
