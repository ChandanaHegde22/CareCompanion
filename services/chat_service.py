"""
services/chat_service.py – AI Companion Chat using Google Gemini.
Maintains per-session conversation history and long-term user memory.
"""

import logging
from datetime import datetime

import config
from database.connection import fetch_all, execute_write, fetch_one
from prompts.companion_prompt import build_companion_prompt
from services.memory_service import format_memories_for_prompt
from utils.emergency_detector import detect_emergency
from utils.translator import translate_to_english, translate_from_english

logger = logging.getLogger(__name__)

LANG_NAMES = {"en": "English", "hi": "Hindi", "kn": "Kannada"}

# ── Gemini initialisation (new google-genai SDK) ───────────────────────────────
_gemini_available = False
_genai_client = None

try:
    from google import genai
    from google.genai import types as genai_types
    if config.GEMINI_API_KEY:
        _genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
    _gemini_available = True
except ImportError:
    try:
        import google.generativeai as _legacy_genai
        if config.GEMINI_API_KEY:
            _legacy_genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_available = True
        _genai_client = "legacy"
    except ImportError:
        logger.error("No Gemini SDK found. Install google-genai or google-generativeai.")


def _call_gemini(system_instruction: str, history: list[dict], user_message: str) -> str:
    """Call Gemini with the new or legacy SDK and return the response text."""
    if not _gemini_available or not config.GEMINI_API_KEY:
        return ""

    # ── New SDK (google-genai) ────────────────────────────────────────────────
    if _genai_client and _genai_client != "legacy":
        try:
            from google.genai import types as t

            # Build contents list from history + current message
            contents = []
            for turn in history:
                contents.append(t.Content(role="user",  parts=[t.Part(text=turn["message"])]))
                contents.append(t.Content(role="model", parts=[t.Part(text=turn["response"])]))
            contents.append(t.Content(role="user", parts=[t.Part(text=user_message)]))

            response = _genai_client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=contents,
                config=t.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.75,
                    max_output_tokens=1024,
                ),
            )
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini (new SDK) error: %s", exc, exc_info=True)
            return ""

    # ── Legacy SDK (google-generativeai) ─────────────────────────────────────
    if _genai_client == "legacy":
        try:
            import google.generativeai as lg
            model = lg.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=system_instruction,
                generation_config=lg.GenerationConfig(
                    temperature=0.75, max_output_tokens=1024
                ),
            )
            gemini_hist = []
            for h in history:
                gemini_hist.append({"role": "user",  "parts": [h["message"]]})
                gemini_hist.append({"role": "model", "parts": [h["response"]]})
            chat  = model.start_chat(history=gemini_hist)
            resp  = chat.send_message(user_message)
            return resp.text.strip()
        except Exception as exc:
            logger.error("Gemini (legacy SDK) error: %s", exc, exc_info=True)
            return ""

    return ""


# ── Public API ────────────────────────────────────────────────────────────────

def send_message(user_id: int, message: str, language: str = "en",
                 session_history: list | None = None) -> dict:
    """
    Send a message to the AI companion and get a response.
    Returns {"success": bool, "response": str, "is_emergency": bool, "emergency_data": dict|None}
    """
    if not message.strip():
        return {"success": False, "response": "Please type a message.", "is_emergency": False}

    # ── Emergency check first ────────────────────────────────────────────────
    emergency_data = detect_emergency(message)

    # ── Translate to English for Gemini if needed ────────────────────────────
    en_message = translate_to_english(message) if language != "en" else message

    # ── Build context ────────────────────────────────────────────────────────
    memory_ctx  = format_memories_for_prompt(user_id)
    lang_name   = LANG_NAMES.get(language, "English")
    system_text = build_companion_prompt(memory_ctx, lang_name)

    # ── Call Gemini ───────────────────────────────────────────────────────────
    hist          = session_history or get_recent_history(user_id, limit=8)
    response_text = _call_gemini(system_text, hist, en_message)

    if not response_text:
        if not config.GEMINI_API_KEY:
            response_text = (
                "👋 I'm here with you! To activate my AI brain, please add "
                "your GEMINI_API_KEY to the .env file. "
                "All other features (medicines, reminders, notes) still work!"
            )
        else:
            response_text = (
                "I'm sorry, I had a little trouble thinking just now. "
                "Could you please try again in a moment?"
            )

    # ── Translate response back if needed ────────────────────────────────────
    if language != "en" and response_text:
        response_text = translate_from_english(response_text, language)

    # ── Persist conversation ─────────────────────────────────────────────────
    try:
        execute_write(
            """INSERT INTO conversations (user_id, message, response, language)
               VALUES (?, ?, ?, ?)""",
            (user_id, message, response_text, language),
        )
    except Exception as exc:
        logger.warning("Failed to persist conversation: %s", exc)

    return {
        "success":        True,
        "response":       response_text,
        "is_emergency":   emergency_data["is_emergency"],
        "emergency_data": emergency_data if emergency_data["is_emergency"] else None,
    }


def get_recent_history(user_id: int, limit: int = 20) -> list[dict]:
    rows = fetch_all(
        """SELECT message, response, language, timestamp
           FROM conversations WHERE user_id=?
           ORDER BY timestamp DESC LIMIT ?""",
        (user_id, limit),
    )
    return list(reversed(rows))


def get_conversation_history(user_id: int, days: int = 7) -> list[dict]:
    from utils.helpers import days_ago
    return fetch_all(
        """SELECT message, response, language, timestamp
           FROM conversations WHERE user_id=? AND timestamp >= ?
           ORDER BY timestamp DESC""",
        (user_id, days_ago(days)),
    )


def clear_history(user_id: int) -> None:
    execute_write("DELETE FROM conversations WHERE user_id=?", (user_id,))


def get_conversation_count(user_id: int) -> int:
    row = fetch_one("SELECT COUNT(*) as cnt FROM conversations WHERE user_id=?", (user_id,))
    return (row or {}).get("cnt", 0)
