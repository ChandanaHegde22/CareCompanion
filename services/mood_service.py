"""
services/mood_service.py – Mood detection and tracking.
Uses Gemini to analyse emotional content; falls back to keyword detection.
"""

import json
import logging
from datetime import date, timedelta

import config
from database.connection import fetch_all, fetch_one, execute_write
from prompts.mood_prompt import build_mood_prompt

logger = logging.getLogger(__name__)

# ── Gemini availability check ─────────────────────────────────────────────────
_gemini_available = False
_genai_client = None

try:
    from google import genai
    if config.GEMINI_API_KEY:
        _genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
    _gemini_available = True
except ImportError:
    try:
        import google.generativeai as _lg
        if config.GEMINI_API_KEY:
            _lg.configure(api_key=config.GEMINI_API_KEY)
        _gemini_available = True
        _genai_client = "legacy"
    except ImportError:
        pass

# Fallback keyword-based mood detection
_MOOD_KEYWORDS = {
    "happy":    ["happy","great","wonderful","excellent","joy","excited","fantastic","delighted"],
    "sad":      ["sad","unhappy","upset","cry","crying","tearful","miss","grief","miserable"],
    "angry":    ["angry","furious","mad","rage","irritated","annoyed","frustrated","livid"],
    "anxious":  ["worried","anxious","nervous","scared","fear","panic","stress","tense","uneasy"],
    "lonely":   ["lonely","alone","isolated","no one","nobody","miss people","abandoned"],
    "confused": ["confused","don't understand","lost","unsure","puzzled","bewildered"],
    "depressed":["depressed","hopeless","worthless","empty","numb","can't go on","pointless"],
    "content":  ["okay","fine","alright","calm","peaceful","relaxed","satisfied"],
}

MOOD_SCORES = {
    "happy":9,"content":7,"neutral":5,"anxious":4,
    "lonely":3,"sad":3,"confused":4,"angry":2,"depressed":1,
}


def _call_gemini_for_mood(text: str) -> dict | None:
    """Call Gemini and parse JSON mood response. Returns None on any failure."""
    if not _gemini_available or not config.GEMINI_API_KEY:
        return None
    prompt = build_mood_prompt(text)
    try:
        raw = ""
        if _genai_client and _genai_client != "legacy":
            from google.genai import types as t
            resp = _genai_client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=t.GenerateContentConfig(temperature=0.3, max_output_tokens=512),
            )
            raw = resp.text.strip()
        else:
            import google.generativeai as lg
            model = lg.GenerativeModel(
                config.GEMINI_MODEL,
                generation_config=lg.GenerationConfig(temperature=0.3, max_output_tokens=512),
            )
            raw = model.generate_content(prompt).text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        if "mood" in data and "mood_score" in data:
            return {
                "mood":            data.get("mood","neutral"),
                "mood_score":      int(data.get("mood_score",5)),
                "triggers":        data.get("triggers",""),
                "suggestions":     data.get("suggestions",""),
                "needs_attention": data.get("needs_attention",False),
            }
    except Exception as exc:
        logger.warning("Gemini mood analysis failed: %s", exc)
    return None


def analyze_mood(text: str) -> dict:
    if not text.strip():
        return _default_mood()
    result = _call_gemini_for_mood(text)
    if result:
        return result
    return _keyword_mood(text)


def _keyword_mood(text: str) -> dict:
    lower = text.lower()
    detected = "neutral"
    for mood, keywords in _MOOD_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            detected = mood
            break
    score = MOOD_SCORES.get(detected, 5)
    return {
        "mood":            detected,
        "mood_score":      score,
        "triggers":        "Based on the words you used",
        "suggestions":     _get_suggestions(detected),
        "needs_attention": score <= 3,
    }


def _default_mood() -> dict:
    return {"mood":"neutral","mood_score":5,"triggers":"","suggestions":"","needs_attention":False}


def _get_suggestions(mood: str) -> str:
    suggestions = {
        "sad":      "Try calling a family member, listen to your favourite music, or take a short walk outside.",
        "angry":    "Take a few deep breaths, drink some water, and give yourself a few quiet minutes.",
        "anxious":  "Practice slow breathing, focus on something pleasant nearby, or write down your worries.",
        "lonely":   "Reach out to a friend or family member, or tell me about your day — I'm listening.",
        "depressed":"Please speak with someone you trust or a healthcare professional. You matter greatly.",
        "confused": "It's okay to feel confused. Let's take it one step at a time — what would you like to clarify?",
        "happy":    "Wonderful! Share your happiness with someone you love, and keep doing what makes you smile.",
        "content":  "Great balance! Maintain it with regular routines, gentle exercise, and nourishing food.",
    }
    return suggestions.get(mood,"Take care of yourself today — small steps make a big difference!")


def log_mood(user_id: int, mood: str, mood_score: int,
             notes: str="", triggers: str="", suggestions: str="") -> int:
    row_id = execute_write(
        """INSERT INTO mood_logs (user_id, mood, mood_score, notes, triggers, suggestions)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, mood, mood_score, notes, triggers, suggestions),
    )
    return row_id


def get_mood_history(user_id: int, days: int=30) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    return fetch_all(
        "SELECT * FROM mood_logs WHERE user_id=? AND logged_at >= ? ORDER BY logged_at DESC",
        (user_id, since),
    )


def get_today_mood(user_id: int) -> dict | None:
    return fetch_one(
        """SELECT * FROM mood_logs WHERE user_id=? AND DATE(logged_at) = DATE('now')
           ORDER BY logged_at DESC LIMIT 1""",
        (user_id,),
    )


def get_mood_statistics(user_id: int, days: int=30) -> dict:
    history = get_mood_history(user_id, days)
    if not history:
        return {"avg_score":0,"mood_counts":{},"trend":"insufficient data","total_logs":0}
    avg_score   = sum(h["mood_score"] for h in history) / len(history)
    mood_counts: dict[str,int] = {}
    for h in history:
        mood_counts[h["mood"]] = mood_counts.get(h["mood"],0) + 1
    dominant = max(mood_counts, key=mood_counts.get)
    recent5  = history[:5]
    trend    = "stable"
    if len(recent5) >= 2:
        recent_avg = sum(h["mood_score"] for h in recent5) / len(recent5)
        older5 = history[5:10]
        if older5:
            older_avg = sum(h["mood_score"] for h in older5) / len(older5)
            trend = "improving" if recent_avg > older_avg+1 else ("declining" if recent_avg < older_avg-1 else "stable")
    return {
        "avg_score":  round(avg_score,1),
        "mood_counts": mood_counts,
        "dominant":   dominant,
        "trend":      trend,
        "total_logs": len(history),
    }
