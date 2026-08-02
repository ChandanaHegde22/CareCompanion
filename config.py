"""
config.py – CareCompanion Central Configuration
All environment variables and application-wide constants live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ── Google Gemini ─────────────────────────────────────────────────────────────
GEMINI_API_KEY: str  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str    = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("SECRET_KEY", "carecompanion-dev-secret-change-in-production")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "carecompanion.db"))

# ── File Storage ──────────────────────────────────────────────────────────────
VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", str(BASE_DIR / "vector_store"))
UPLOADS_PATH: str      = os.getenv("UPLOADS_PATH",      str(BASE_DIR / "uploads"))
LOGS_PATH: str         = os.getenv("LOGS_PATH",         str(BASE_DIR / "logs"))
MAX_UPLOAD_MB: int     = int(os.getenv("MAX_UPLOAD_MB", "20"))

# ── Twilio SMS ────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID: str   = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN: str    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER: str  = os.getenv("TWILIO_PHONE_NUMBER", "")

# ── Email ─────────────────────────────────────────────────────────────────────
SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL: str       = os.getenv("FROM_EMAIL", "noreply@carecompanion.ai")

# ── App Meta ──────────────────────────────────────────────────────────────────
APP_NAME: str    = os.getenv("APP_NAME", "CareCompanion")
APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
DEBUG: bool      = os.getenv("DEBUG", "False").lower() == "true"

# ── Embedding Model (Sentence-Transformers) ───────────────────────────────────
EMBEDDING_MODEL: str  = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int    = 384
CHUNK_SIZE: int       = 500
CHUNK_OVERLAP: int    = 50
RAG_TOP_K: int        = 5

# ── Supported Languages ───────────────────────────────────────────────────────
LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
}

# ── Mood Labels & Scores ──────────────────────────────────────────────────────
MOODS: dict[str, dict] = {
    "happy":    {"emoji": "😊", "score": 9, "color": "#4CAF50"},
    "content":  {"emoji": "😌", "score": 7, "color": "#8BC34A"},
    "neutral":  {"emoji": "😐", "score": 5, "color": "#9E9E9E"},
    "anxious":  {"emoji": "😰", "score": 4, "color": "#FF9800"},
    "lonely":   {"emoji": "😔", "score": 3, "color": "#FF7043"},
    "sad":      {"emoji": "😢", "score": 3, "color": "#2196F3"},
    "confused": {"emoji": "😕", "score": 4, "color": "#9C27B0"},
    "angry":    {"emoji": "😠", "score": 2, "color": "#F44336"},
    "depressed":{"emoji": "😞", "score": 1, "color": "#37474F"},
}

# ── Reminder Types ────────────────────────────────────────────────────────────
REMINDER_TYPES: list[str] = [
    "Wake Up", "Breakfast", "Exercise", "Walk",
    "Yoga", "Lunch", "Doctor Visit", "Family Call",
    "Dinner", "Medication", "Sleep", "General"
]

# ── Emergency Keywords ────────────────────────────────────────────────────────
EMERGENCY_KEYWORDS: list[str] = [
    "i fell", "fell down", "i can't breathe", "cant breathe", "cannot breathe",
    "chest pain", "heart attack", "help me", "emergency", "call 911",
    "i'm dying", "im dying", "stroke", "bleeding", "unconscious",
    "severe pain", "ambulance", "fainted", "can't move", "cant move",
    "help", "sos", "attack", "overdose", "poisoning", "choking",
]

# ── Ensure directories exist ──────────────────────────────────────────────────
for _path in (UPLOADS_PATH, VECTOR_STORE_PATH, LOGS_PATH,
              str(Path(DATABASE_PATH).parent)):
    Path(_path).mkdir(parents=True, exist_ok=True)
