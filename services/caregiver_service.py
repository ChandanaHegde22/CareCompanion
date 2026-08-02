"""
services/caregiver_service.py – Caregiver dashboard data aggregation.
"""

import logging
from database.connection import fetch_all, fetch_one, execute_write
from utils.helpers import days_ago

logger = logging.getLogger(__name__)


def get_dashboard_data(elderly_user_id: int) -> dict:
    """
    Aggregate all data needed for the caregiver dashboard in one call.
    Returns a dict with medicine, mood, emergency, chat, reminder stats.
    """
    from services.medicine_service   import get_adherence_stats, get_today_medicines
    from services.mood_service       import get_mood_statistics, get_mood_history
    from services.emergency_service  import get_emergency_logs, get_emergency_stats
    from services.reminder_service   import get_completion_stats, get_today_reminders
    from services.chat_service       import get_conversation_count
    from services.notes_service      import get_notes_count

    user = fetch_one(
        "SELECT id, full_name, username, age, last_login FROM users WHERE id=?",
        (elderly_user_id,),
    )

    return {
        "user":             dict(user) if user else {},
        "medicine_stats":   get_adherence_stats(elderly_user_id, days=7),
        "today_medicines":  get_today_medicines(elderly_user_id),
        "mood_stats":       get_mood_statistics(elderly_user_id, days=30),
        "mood_history":     get_mood_history(elderly_user_id, days=14),
        "emergency_stats":  get_emergency_stats(elderly_user_id),
        "recent_emergencies": get_emergency_logs(elderly_user_id, limit=5),
        "reminder_stats":   get_completion_stats(elderly_user_id, days=7),
        "today_reminders":  get_today_reminders(elderly_user_id),
        "conversation_count": get_conversation_count(elderly_user_id),
        "notes_count":      get_notes_count(elderly_user_id),
    }


def add_caregiver(elderly_user_id: int, caregiver_username: str,
                  permission_level: str = "view") -> dict:
    caregiver = fetch_one(
        "SELECT id FROM users WHERE username=?", (caregiver_username.strip().lower(),)
    )
    if not caregiver:
        return {"success": False,
                "message": f"User '{caregiver_username}' not found in CareCompanion."}
    existing = fetch_one(
        "SELECT id FROM caregivers WHERE user_id=? AND caregiver_username=?",
        (elderly_user_id, caregiver_username.strip().lower()),
    )
    if existing:
        return {"success": False, "message": "This caregiver is already linked."}
    execute_write(
        "INSERT INTO caregivers (user_id, caregiver_username, permission_level) VALUES (?, ?, ?)",
        (elderly_user_id, caregiver_username.strip().lower(), permission_level),
    )
    return {"success": True,
            "message": f"Caregiver '{caregiver_username}' linked successfully!"}


def get_caregivers(elderly_user_id: int) -> list[dict]:
    return fetch_all(
        "SELECT * FROM caregivers WHERE user_id=? ORDER BY added_at DESC",
        (elderly_user_id,),
    )


def remove_caregiver(caregiver_id: int) -> dict:
    execute_write("DELETE FROM caregivers WHERE id=?", (caregiver_id,))
    return {"success": True, "message": "Caregiver removed."}


def get_linked_patients(caregiver_username: str) -> list[dict]:
    """Return all elderly users that a caregiver is linked to."""
    rows = fetch_all(
        "SELECT user_id, permission_level FROM caregivers WHERE caregiver_username=?",
        (caregiver_username.lower(),),
    )
    result = []
    for r in rows:
        user = fetch_one(
            "SELECT id, full_name, username, age FROM users WHERE id=?",
            (r["user_id"],),
        )
        if user:
            result.append({**dict(user), "permission": r["permission_level"]})
    return result
