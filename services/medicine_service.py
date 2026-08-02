"""
services/medicine_service.py – Medicine management and adherence tracking.
"""

import json
import logging
from datetime import datetime, date, timedelta

from database.connection import fetch_all, fetch_one, execute_write
from utils.helpers import to_json, from_json, today_str, now_str

logger = logging.getLogger(__name__)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_medicine(user_id: int, name: str, dosage: str, frequency: str,
                 times: list[str], meal_timing: str = "anytime",
                 start_date: str = "", end_date: str = "", notes: str = "") -> dict:
    """Add a new medicine for a user."""
    if not name.strip():
        return {"success": False, "message": "Medicine name is required."}
    if not times:
        return {"success": False, "message": "At least one reminder time is required."}

    med_id = execute_write(
        """INSERT INTO medicines
           (user_id, name, dosage, frequency, times, meal_timing, start_date, end_date, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name.strip(), dosage.strip(), frequency,
         to_json(times), meal_timing,
         start_date or today_str(), end_date or "", notes.strip()),
    )
    logger.info("Medicine added: %s for user %s", name, user_id)
    return {"success": True, "message": f"'{name}' added to your medicines!", "medicine_id": med_id}


def get_medicines(user_id: int, active_only: bool = True) -> list[dict]:
    sql = "SELECT * FROM medicines WHERE user_id=?"
    params: tuple = (user_id,)
    if active_only:
        sql += " AND is_active=1"
    sql += " ORDER BY name"
    rows = fetch_all(sql, params)
    for r in rows:
        r["times"] = from_json(r.get("times", "[]"), [])
    return rows


def get_medicine(medicine_id: int) -> dict | None:
    row = fetch_one("SELECT * FROM medicines WHERE id=?", (medicine_id,))
    if row:
        row["times"] = from_json(row.get("times", "[]"), [])
    return row


def update_medicine(medicine_id: int, name: str, dosage: str, frequency: str,
                    times: list[str], meal_timing: str, end_date: str = "",
                    notes: str = "") -> dict:
    execute_write(
        """UPDATE medicines
           SET name=?, dosage=?, frequency=?, times=?, meal_timing=?, end_date=?, notes=?
           WHERE id=?""",
        (name.strip(), dosage.strip(), frequency, to_json(times),
         meal_timing, end_date, notes.strip(), medicine_id),
    )
    return {"success": True, "message": "Medicine updated!"}


def delete_medicine(medicine_id: int) -> dict:
    execute_write("UPDATE medicines SET is_active=0 WHERE id=?", (medicine_id,))
    return {"success": True, "message": "Medicine removed."}


# ── Adherence / Logs ──────────────────────────────────────────────────────────

def log_medicine_taken(user_id: int, medicine_id: int,
                       scheduled_time: str, notes: str = "") -> dict:
    """Mark a medicine as taken."""
    # Check if already marked
    existing = fetch_one(
        "SELECT id, status FROM medicine_logs WHERE user_id=? AND medicine_id=? AND scheduled_time=?",
        (user_id, medicine_id, scheduled_time),
    )
    if existing:
        if existing["status"] == "taken":
            return {"success": False, "message": "Already marked as taken."}
        execute_write(
            "UPDATE medicine_logs SET status='taken', taken_time=?, notes=? WHERE id=?",
            (now_str(), notes, existing["id"]),
        )
    else:
        execute_write(
            """INSERT INTO medicine_logs (user_id, medicine_id, scheduled_time, taken_time, status, notes)
               VALUES (?, ?, ?, ?, 'taken', ?)""",
            (user_id, medicine_id, scheduled_time, now_str(), notes),
        )
    return {"success": True, "message": "Medicine marked as taken ✅"}


def log_medicine_missed(user_id: int, medicine_id: int, scheduled_time: str) -> None:
    execute_write(
        """INSERT OR IGNORE INTO medicine_logs
           (user_id, medicine_id, scheduled_time, status)
           VALUES (?, ?, ?, 'missed')""",
        (user_id, medicine_id, scheduled_time),
    )


def get_medicine_logs(user_id: int, days: int = 7) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    return fetch_all(
        """SELECT ml.*, m.name AS medicine_name, m.dosage
           FROM medicine_logs ml
           JOIN medicines m ON ml.medicine_id = m.id
           WHERE ml.user_id=? AND ml.scheduled_time >= ?
           ORDER BY ml.scheduled_time DESC""",
        (user_id, since),
    )


def get_today_medicines(user_id: int) -> list[dict]:
    """Return all active medicines with their status for today."""
    medicines = get_medicines(user_id)
    today     = today_str()
    result    = []
    for med in medicines:
        for t in med["times"]:
            scheduled = f"{today} {t}"
            log = fetch_one(
                "SELECT status FROM medicine_logs WHERE user_id=? AND medicine_id=? AND scheduled_time=?",
                (user_id, med["id"], scheduled),
            )
            status = log["status"] if log else "pending"
            result.append({
                **med,
                "scheduled_time": scheduled,
                "time_slot":      t,
                "status":         status,
            })
    result.sort(key=lambda x: x["time_slot"])
    return result


def get_adherence_stats(user_id: int, days: int = 7) -> dict:
    """Calculate medication adherence percentage."""
    logs  = get_medicine_logs(user_id, days)
    if not logs:
        return {"adherence_pct": 0, "taken": 0, "missed": 0, "pending": 0, "total": 0}

    counts = {"taken": 0, "missed": 0, "skipped": 0, "pending": 0}
    for log in logs:
        s = log.get("status", "pending")
        counts[s] = counts.get(s, 0) + 1

    total = len(logs)
    taken = counts["taken"]
    pct   = round((taken / total) * 100, 1) if total else 0
    return {
        "adherence_pct": pct,
        "taken":         taken,
        "missed":        counts["missed"],
        "pending":       counts["pending"],
        "total":         total,
    }
