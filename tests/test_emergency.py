"""tests/test_emergency.py – Emergency detection and logging tests."""
import pytest, uuid


def uid():
    from services.auth_service import register_user
    u = f"em_{uuid.uuid4().hex[:8]}"
    r = register_user(u, f"{u}@ex.com", "Pass1234!")
    return r["user_id"]


class TestEmergencyDetection:
    def _d(self, text):
        from utils.emergency_detector import detect_emergency
        return detect_emergency(text)

    # ── Positive cases ────────────────────────────────────────────────────────
    def test_fall_detected(self):
        r = self._d("I fell down in the bathroom")
        assert r["is_emergency"] is True and r["emergency_type"] == "fall"

    def test_chest_pain_detected(self):
        r = self._d("I have severe chest pain")
        assert r["is_emergency"] is True and r["emergency_type"] == "cardiac"

    def test_breathing_detected(self):
        r = self._d("I cannot breathe, I am choking")
        assert r["is_emergency"] is True and r["emergency_type"] == "breathing"

    def test_stroke_detected(self):
        r = self._d("I think I am having a stroke")
        assert r["is_emergency"] is True and r["emergency_type"] == "stroke"

    def test_help_triggers_emergency(self):
        r = self._d("Help me! Emergency!")
        assert r["is_emergency"] is True

    def test_sos_detected(self):
        r = self._d("SOS please help")
        assert r["is_emergency"] is True

    def test_severe_pain_detected(self):
        r = self._d("I have severe pain that is unbearable")
        assert r["is_emergency"] is True and r["emergency_type"] == "severe_pain"

    def test_overdose_detected(self):
        r = self._d("I think I took an overdose of my medication")
        assert r["is_emergency"] is True and r["emergency_type"] == "medical"

    def test_heart_attack_detected(self):
        r = self._d("heart attack happening now")
        assert r["is_emergency"] is True

    def test_bleeding_detected(self):
        r = self._d("I am bleeding heavily")
        assert r["is_emergency"] is True

    # ── Negative cases ────────────────────────────────────────────────────────
    def test_normal_message_no_emergency(self):
        r = self._d("Good morning! How are you today?")
        assert r["is_emergency"] is False

    def test_empty_text_no_emergency(self):
        r = self._d("")
        assert r["is_emergency"] is False

    def test_medicine_question_no_emergency(self):
        r = self._d("What time should I take my medicine?")
        assert r["is_emergency"] is False

    def test_mild_headache_no_emergency(self):
        r = self._d("I have a mild headache from reading too long")
        assert r["is_emergency"] is False

    # ── Severity levels ───────────────────────────────────────────────────────
    def test_cardiac_critical(self):
        r = self._d("I am having a heart attack")
        assert r["severity"] == "critical"

    def test_stroke_critical(self):
        r = self._d("I think I am having a stroke")
        assert r["severity"] == "critical"

    def test_fall_medium(self):
        r = self._d("I fell down")
        assert r["severity"] == "medium"

    # ── Confidence ────────────────────────────────────────────────────────────
    def test_confidence_in_range(self):
        r = self._d("chest pain cardiac emergency")
        assert 0.0 <= r["confidence"] <= 1.0

    def test_more_keywords_higher_confidence(self):
        r_single   = self._d("help")
        r_multiple = self._d("help emergency fell chest pain cardiac")
        assert r_multiple["confidence"] >= r_single["confidence"]


class TestEmergencyMessages:
    def test_cardiac_message(self):
        from utils.emergency_detector import get_emergency_message
        msg = get_emergency_message("cardiac").lower()
        assert any(w in msg for w in ["call", "emergency", "services", "now", "911", "108"])

    def test_fall_message_exists(self):
        from utils.emergency_detector import get_emergency_message
        assert len(get_emergency_message("fall")) > 20

    def test_unknown_type_has_default(self):
        from utils.emergency_detector import get_emergency_message
        assert len(get_emergency_message("unknown_type_xyz")) > 10


class TestEmergencyLogging:
    def test_log_and_retrieve(self):
        from services.emergency_service import log_emergency, get_emergency_logs
        user_id = uid()
        eid = log_emergency(user_id, "I fell down", "fall", "medium")
        assert eid > 0
        logs = get_emergency_logs(user_id)
        assert len(logs) >= 1 and logs[0]["emergency_type"] == "fall"

    def test_resolve_emergency(self):
        from services.emergency_service import log_emergency, resolve_emergency, get_emergency_logs
        user_id = uid()
        eid = log_emergency(user_id, "chest pain", "cardiac", "critical")
        resolve_emergency(eid)
        logs = get_emergency_logs(user_id)
        resolved = next(l for l in logs if l["id"] == eid)
        assert resolved["resolved_at"] is not None

    def test_emergency_stats(self):
        from services.emergency_service import log_emergency, get_emergency_stats
        user_id = uid()
        log_emergency(user_id, "fell",  "fall",    "medium")
        log_emergency(user_id, "chest", "cardiac", "critical")
        log_emergency(user_id, "help",  "general", "high")
        stats = get_emergency_stats(user_id)
        assert stats["total"] == 3
        assert "fall" in stats["by_type"]

    def test_notify_no_contacts(self):
        from services.emergency_service import log_emergency, notify_emergency_contacts
        user_id = uid()
        eid = log_emergency(user_id, "help", "general", "high")
        notif = notify_emergency_contacts(user_id, eid, "general", "help")
        assert notif["sms_sent"] == 0 and notif["email_sent"] == 0


class TestValidators:
    def test_valid_emails(self):
        from utils.validators import validate_email
        assert validate_email("user@example.com") is True
        assert validate_email("name+tag@domain.co.in") is True

    def test_invalid_emails(self):
        from utils.validators import validate_email
        assert validate_email("not-an-email") is False
        assert validate_email("") is False

    def test_valid_phone(self):
        from utils.validators import validate_phone
        assert validate_phone("+919876543210") is True
        assert validate_phone("9876543210") is True

    def test_invalid_phone(self):
        from utils.validators import validate_phone
        assert validate_phone("123") is False

    def test_valid_password(self):
        from utils.validators import validate_password
        assert validate_password("Password1!") is True
        assert validate_password("12345678") is True

    def test_invalid_password(self):
        from utils.validators import validate_password
        assert validate_password("short") is False

    def test_sanitize_text(self):
        from utils.validators import sanitize_text
        assert sanitize_text("  hello  ") == "hello"
        assert len(sanitize_text("a" * 2000, max_length=100)) == 100
