"""
services/reminder_service.py – Daily routine reminders and task tracking.
"""

import logging
from datetime import date

from database.connection import fetch_all, fetch_one, execute_write
from utils.helpers import to_json, from_json, today_str, get_current_weekday, now_str

logger = logging.getLogger(__name__)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_reminder(user_id: int, title: str, description: str,
                 reminder_type: str, time: str, days: list[str]) -> dict:
    if not title.strip():
        return {"success": False, "message": "Reminder title is required."}
    if not time:
        return {"success": False, "message": "Time is required."}
    if not days:
        return {"success": False, "message": "Select at least one day."}

    rid = execute_write(
        """INSERT INTO reminders (user_id, title, description, reminder_type, time, days)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, title.strip(), description.strip(), reminder_type,
         time, to_json([d.lower() for d in days])),
    )
    return {"success": True, "message": f"Reminder '{title}' added!", "reminder_id": rid}


def get_reminders(user_id: int, active_only: bool = True) -> list[dict]:
    sql = "SELECT * FROM reminders WHERE user_id=?"
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY time"
    rows = fetch_all(sql, (user_id,))
    for r in rows:
        r["days"] = from_json(r.get("days", "[]"), [])
    return rows


def get_reminder(reminder_id: int) -> dict | None:
    row = fetch_one("SELECT * FROM reminders WHERE id=?", (reminder_id,))
    if row:
        row["days"] = from_json(row.get("days", "[]"), [])
    return row


def update_reminder(reminder_id: int, title: str, description: str,
                    reminder_type: str, time: str, days: list[str]) -> dict:
    execute_write(
        """UPDATE reminders
           SET title=?, description=?, reminder_type=?, time=?, days=?
           WHERE id=?""",
        (title.strip(), description.strip(), reminder_type,
         time, to_json([d.lower() for d in days]), reminder_id),
    )
    return {"success": True, "message": "Reminder updated!"}


def toggle_reminder(reminder_id: int, active: bool) -> dict:
    execute_write(
        "UPDATE reminders SET is_active=? WHERE id=?",
        (1 if active else 0, reminder_id),
    )
    state = "enabled" if active else "disabled"
    return {"success": True, "message": f"Reminder {state}."}


def delete_reminder(reminder_id: int) -> dict:
    execute_write("DELETE FROM reminders WHERE id=?", (reminder_id,))
    return {"success": True, "message": "Reminder deleted."}


# ── Today's Reminders ─────────────────────────────────────────────────────────

def get_today_reminders(user_id: int) -> list[dict]:
    """Return all reminders for today with their completion status."""
    all_reminders = get_reminders(user_id)
    weekday       = get_current_weekday()
    today         = today_str()
    result        = []

    for rem in all_reminders:
        if weekday not in (rem.get("days") or []):
            continue
        scheduled = f"{today} {rem['time']}"
        log       = fetch_one(
            "SELECT status FROM reminder_logs WHERE user_id=? AND reminder_id=? AND scheduled_time=?",
            (user_id, rem["id"], scheduled),
        )
        result.append({
            **rem,
            "scheduled_time": scheduled,
            "status": log["status"] if log else "pending",
        })

    result.sort(key=lambda x: x["time"])
    return result


def complete_reminder(user_id: int, reminder_id: int, scheduled_time: str) -> dict:
    existing = fetch_one(
        "SELECT id FROM reminder_logs WHERE user_id=? AND reminder_id=? AND scheduled_time=?",
        (user_id, reminder_id, scheduled_time),
    )
    if existing:
        execute_write(
            "UPDATE reminder_logs SET status='completed', completed_time=? WHERE id=?",
            (now_str(), existing["id"]),
        )
    else:
        execute_write(
            """INSERT INTO reminder_logs (user_id, reminder_id, scheduled_time, completed_time, status)
               VALUES (?, ?, ?, ?, 'completed')""",
            (user_id, reminder_id, scheduled_time, now_str()),
        )
    return {"success": True, "message": "✅ Marked as done!"}


# ── Statistics ────────────────────────────────────────────────────────────────

def get_completion_stats(user_id: int, days: int = 7) -> dict:
    from utils.helpers import days_ago
    logs = fetch_all(
        """SELECT status FROM reminder_logs
           WHERE user_id=? AND scheduled_time >= ?""",
        (user_id, days_ago(days)),
    )
    if not logs:
        return {"completion_pct": 0, "completed": 0, "missed": 0, "total": 0}
    completed = sum(1 for l in logs if l["status"] == "completed")
    total     = len(logs)
    return {
        "completion_pct": round((completed / total) * 100, 1) if total else 0,
        "completed":      completed,
        "missed":         total - completed,
        "total":          total,
    }
