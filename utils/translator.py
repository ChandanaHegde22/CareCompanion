"""
utils/translator.py – CareCompanion Translation Utilities
Supports English, Hindi, and Kannada via deep-translator (Google backend).
"""

import logging

logger = logging.getLogger(__name__)

# Language code mapping
LANG_CODES = {
    "en": "english",
    "hi": "hindi",
    "kn": "kannada",
}

_translator_available = False
try:
    from deep_translator import GoogleTranslator
    _translator_available = True
except ImportError:
    logger.warning("deep-translator not installed; translation disabled.")


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate *text* to *target_lang*.
    Falls back to returning original text if translation fails or is unavailable.
    """
    if not text or not text.strip():
        return text
    if target_lang == "en" and source_lang in ("en", "auto"):
        return text
    if not _translator_available:
        return text
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text) or text
    except Exception as exc:
        logger.warning("Translation failed (%s→%s): %s", source_lang, target_lang, exc)
        return text


def translate_to_english(text: str) -> str:
    return translate_text(text, "en", "auto")


def translate_from_english(text: str, target_lang: str) -> str:
    if target_lang == "en":
        return text
    return translate_text(text, target_lang, "en")


def get_ui_label(key: str, lang: str) -> str:
    """
    Return a UI label in the target language.
    Falls back to English if not available.
    """
    labels = {
        "greeting": {
            "en": "Hello",
            "hi": "नमस्ते",
            "kn": "ನಮಸ್ಕಾರ",
        },
        "how_are_you": {
            "en": "How are you feeling today?",
            "hi": "आज आप कैसा महसूस कर रहे हैं?",
            "kn": "ಇಂದು ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        },
        "ask_question": {
            "en": "Ask me anything…",
            "hi": "कुछ भी पूछें…",
            "kn": "ಏನಾದರೂ ಕೇಳಿ…",
        },
        "emergency_detected": {
            "en": "🚨 Emergency Detected! Contacting help immediately.",
            "hi": "🚨 आपातकाल का पता चला! तत्काल मदद के लिए संपर्क किया जा रहा है।",
            "kn": "🚨 ತುರ್ತು ಪರಿಸ್ಥಿತಿ ಪತ್ತೆಯಾಗಿದೆ! ತಕ್ಷಣ ಸಹಾಯ ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ.",
        },
    }
    return labels.get(key, {}).get(lang, labels.get(key, {}).get("en", key))
