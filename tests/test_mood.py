"""tests/test_mood.py – Mood detection and tracking tests."""
import pytest
import uuid


def uid():
    from services.auth_service import register_user
    u = f"mood_{uuid.uuid4().hex[:8]}"
    r = register_user(u, f"{u}@ex.com", "Pass1234!")
    return r["user_id"]


class TestKeywordMoodDetection:
    def _kw(self, text):
        from services.mood_service import _keyword_mood
        return _keyword_mood(text)

    def test_happy(self):
        r = self._kw("I am feeling so happy and wonderful today!")
        assert r["mood"] == "happy" and r["mood_score"] >= 8

    def test_sad(self):
        r = self._kw("I am very sad and crying. I miss my family.")
        assert r["mood"] == "sad" and r["mood_score"] <= 4

    def test_anxious(self):
        r = self._kw("I am very worried and stressed about my health.")
        assert r["mood"] == "anxious"

    def test_lonely(self):
        r = self._kw("I feel lonely. Nobody visits me and I am alone.")
        assert r["mood"] == "lonely"

    def test_angry(self):
        r = self._kw("I am so angry and furious about what happened.")
        assert r["mood"] == "angry" and r["mood_score"] <= 3

    def test_depressed(self):
        r = self._kw("I feel completely hopeless and worthless.")
        assert r["mood"] == "depressed" and r["mood_score"] == 1

    def test_empty_returns_neutral(self):
        from services.mood_service import analyze_mood
        r = analyze_mood("")
        assert r["mood"] == "neutral" and r["mood_score"] == 5

    def test_needs_attention_low_score(self):
        r = self._kw("I feel hopeless and depressed.")
        assert r["needs_attention"] is True

    def test_needs_attention_false_for_happy(self):
        r = self._kw("I am so happy and wonderful!")
        assert r["needs_attention"] is False


class TestMoodLogging:
    def test_log_and_retrieve(self):
        from services.mood_service import log_mood, get_mood_history
        user_id = uid()
        row_id = log_mood(user_id, "happy", 8, notes="Feeling great")
        assert row_id > 0
        h = get_mood_history(user_id, days=1)
        assert len(h) >= 1 and h[0]["mood"] == "happy"

    def test_get_today_mood(self):
        from services.mood_service import log_mood, get_today_mood
        user_id = uid()
        log_mood(user_id, "content", 7)
        t = get_today_mood(user_id)
        assert t is not None and t["mood"] == "content"

    def test_mood_statistics(self):
        from services.mood_service import log_mood, get_mood_statistics
        user_id = uid()
        log_mood(user_id, "happy", 9)
        log_mood(user_id, "sad", 3)
        log_mood(user_id, "neutral", 5)
        s = get_mood_statistics(user_id, days=30)
        assert s["total_logs"] >= 3
        assert 0 < s["avg_score"] <= 10

    def test_empty_history_statistics(self):
        from services.mood_service import get_mood_statistics
        user_id = uid()
        s = get_mood_statistics(user_id, days=30)
        assert s["avg_score"] == 0 and s["total_logs"] == 0


class TestMoodSuggestions:
    def test_sad_suggestion(self):
        from services.mood_service import _get_suggestions
        s = _get_suggestions("sad")
        assert len(s) > 20

    def test_depressed_suggestion_mentions_help(self):
        from services.mood_service import _get_suggestions
        s = _get_suggestions("depressed").lower()
        assert any(w in s for w in ["professional", "healthcare", "trust", "alone"])

    def test_happy_suggestion_positive(self):
        from services.mood_service import _get_suggestions
        s = _get_suggestions("happy").lower()
        assert any(w in s for w in ["smile", "love", "wonderful", "share", "happy"])
