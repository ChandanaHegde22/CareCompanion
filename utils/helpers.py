"""
utils/helpers.py – CareCompanion General Utilities
"""

import json
import logging
import os
from datetime import datetime, date, timedelta
from pathlib import Path

import config

logger = logging.getLogger(__name__)


# ── JSON helpers ──────────────────────────────────────────────────────────────

def to_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def from_json(s: str, default=None):
    try:
        return json.loads(s)
    except Exception:
        return default


# ── Date / Time helpers ───────────────────────────────────────────────────────

def now_str() -> str:
    return datetime.now().isoformat(timespec="seconds")


def today_str() -> str:
    return date.today().isoformat()


def format_datetime(dt_str: str) -> str:
    """Convert ISO string to readable format."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return dt_str or "—"


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def get_week_dates() -> list[str]:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]


def get_current_weekday() -> str:
    return date.today().strftime("%A").lower()


# ── File helpers ──────────────────────────────────────────────────────────────

def get_user_upload_dir(user_id: int) -> Path:
    path = Path(config.UPLOADS_PATH) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_vector_store_path(user_id: int) -> Path:
    path = Path(config.VECTOR_STORE_PATH) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_file(user_id: int, uploaded_file) -> str:
    """Save a Streamlit UploadedFile to disk and return its path."""
    dest = get_user_upload_dir(user_id) / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.info("Saved upload: %s", dest)
    return str(dest)


def file_size_mb(path: str) -> float:
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except OSError:
        return 0.0


# ── Colour / Emoji helpers ────────────────────────────────────────────────────

WEEKDAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_NAMES = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec",
]


def adherence_color(pct: float) -> str:
    """Return a colour hex based on adherence percentage."""
    if pct >= 80:
        return "#4CAF50"
    if pct >= 50:
        return "#FF9800"
    return "#F44336"


def severity_emoji(severity: str) -> str:
    return {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(severity.lower(), "⚪")


def truncate(text: str, max_len: int = 80) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "…"


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure application-wide logging to file + console."""
    log_file = Path(config.LOGS_PATH) / "carecompanion.log"
    logging.basicConfig(
        level=logging.INFO if not config.DEBUG else logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
