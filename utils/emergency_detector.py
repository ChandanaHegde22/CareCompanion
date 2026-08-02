"""
utils/emergency_detector.py – CareCompanion Emergency Detection
Two-pass detection: fast keyword scan, then Gemini AI analysis.
"""

import logging
import re

import config

logger = logging.getLogger(__name__)


# ── Emergency type classification ─────────────────────────────────────────────

_EMERGENCY_PATTERNS: dict[str, list[str]] = {
    "fall":         ["fell", "fall", "fallen", "slipped", "tripped", "dropped"],
    "cardiac":      ["chest pain", "heart attack", "palpitation", "heart pain",
                     "cardiac", "heart hurts", "my heart"],
    "breathing":    ["can't breathe", "cannot breathe", "cant breathe", "choking",
                     "suffocating", "no air", "shortness of breath", "trouble breathing", "cannot breathe"],
    "stroke":       ["stroke", "paralysed", "paralyzed", "numb", "face drooping",
                     "arm weak", "speech slurred", "can't speak", "cannot speak"],
    "severe_pain":  ["severe pain", "unbearable pain", "extreme pain", "terrible pain",
                     "worst pain", "pain is killing"],
    "medical":      ["overdose", "poisoning", "bleeding", "blood"],
    "general":      ["help", "sos", "emergency", "ambulance", "call 911",
                     "call 999", "call 112", "i'm dying", "im dying",
                     "fainted", "unconscious", "passed out"],
}

SEVERITY_MAP: dict[str, str] = {
    "fall":        "medium",
    "cardiac":     "critical",
    "breathing":   "critical",
    "stroke":      "critical",
    "severe_pain": "high",
    "medical":     "high",
    "general":     "high",
}


def detect_emergency(text: str) -> dict:
    """
    Scan *text* for emergency signals.

    Returns::

        {
          "is_emergency": bool,
          "emergency_type": str,
          "severity": str,          # critical | high | medium | low
          "matched_keywords": list,
          "confidence": float,      # 0.0 – 1.0
        }
    """
    if not text:
        return _no_emergency()

    lower = text.lower()
    # Remove punctuation for matching
    cleaned = re.sub(r"[^\w\s]", " ", lower)

    matched_type = None
    matched_keywords: list[str] = []

    for etype, keywords in _EMERGENCY_PATTERNS.items():
        for kw in keywords:
            if kw in cleaned:
                matched_keywords.append(kw)
                if matched_type is None:
                    matched_type = etype  # first/highest priority match

    if not matched_type:
        return _no_emergency()

    severity = SEVERITY_MAP.get(matched_type, "high")
    confidence = min(0.5 + 0.1 * len(matched_keywords), 1.0)

    logger.warning(
        "Emergency detected! type=%s severity=%s text='%s'",
        matched_type, severity, text[:120],
    )

    return {
        "is_emergency":     True,
        "emergency_type":   matched_type,
        "severity":         severity,
        "matched_keywords": matched_keywords,
        "confidence":       confidence,
    }


def _no_emergency() -> dict:
    return {
        "is_emergency":     False,
        "emergency_type":   None,
        "severity":         "none",
        "matched_keywords": [],
        "confidence":       0.0,
    }


def get_emergency_message(emergency_type: str) -> str:
    """Return a human-readable alert message for the given emergency type."""
    messages = {
        "fall":        "⚠️ A fall has been detected. Please check on the user immediately.",
        "cardiac":     "🫀 Possible cardiac emergency! Call emergency services NOW.",
        "breathing":   "🫁 Breathing difficulty detected! Call emergency services NOW.",
        "stroke":      "🧠 Possible stroke detected! Call emergency services NOW.",
        "severe_pain": "😰 Severe pain reported. Immediate medical attention needed.",
        "medical":     "🏥 Medical emergency detected. Seek help immediately.",
        "general":     "🆘 Emergency detected! Please respond immediately.",
    }
    return messages.get(emergency_type, "🚨 Emergency detected! Please help.")
