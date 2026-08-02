"""
scheduler/reminder_scheduler.py – Background reminder scheduler using APScheduler.
Fires medicine and routine reminder jobs without blocking the Streamlit UI.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler_started = False
_scheduler = None

_apscheduler_available = False
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron        import CronTrigger
    _apscheduler_available = True
except ImportError:
    logger.warning("APScheduler not installed. Background reminders disabled.")


import streamlit as st

@st.cache_resource
def get_scheduler():
    """Return the singleton BackgroundScheduler, starting it if needed."""
    global _scheduler, _scheduler_started
    if not _apscheduler_available:
        return None
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            timezone="UTC",
            job_defaults={"coalesce": True, "max_instances": 1},
        )
    if not _scheduler.running:
        try:
            _scheduler.start()
            _scheduler_started = True
            logger.info("Background scheduler started.")
        except Exception as exc:
            logger.error("Failed to start scheduler: %s", exc)
    return _scheduler


def schedule_medicine_reminder(user_id: int, medicine_id: int,
                                medicine_name: str, time_str: str) -> bool:
    """
    Schedule a daily medicine reminder at HH:MM.
    Job ID format: med_{user_id}_{medicine_id}_{HH}_{MM}
    """
    scheduler = get_scheduler()
    if scheduler is None:
        return False
    try:
        h, m  = time_str.split(":")
        job_id = f"med_{user_id}_{medicine_id}_{h}_{m}"
        scheduler.add_job(
            _medicine_reminder_job,
            CronTrigger(hour=int(h), minute=int(m)),
            id=job_id,
            replace_existing=True,
            args=[user_id, medicine_id, medicine_name, time_str],
            name=f"Medicine: {medicine_name} at {time_str}",
        )
        logger.info("Scheduled medicine reminder: %s", job_id)
        return True
    except Exception as exc:
        logger.error("Failed to schedule medicine reminder: %s", exc)
        return False


def schedule_routine_reminder(user_id: int, reminder_id: int,
                               title: str, time_str: str, days: list[str]) -> bool:
    """Schedule a routine reminder on specific days of the week."""
    scheduler = get_scheduler()
    if scheduler is None:
        return False
    try:
        h, m   = time_str.split(":")
        day_of_week = ",".join([_day_abbr(d) for d in days])
        job_id = f"rem_{user_id}_{reminder_id}"
        scheduler.add_job(
            _routine_reminder_job,
            CronTrigger(hour=int(h), minute=int(m), day_of_week=day_of_week),
            id=job_id,
            replace_existing=True,
            args=[user_id, reminder_id, title, time_str],
            name=f"Reminder: {title} at {time_str}",
        )
        logger.info("Scheduled routine reminder: %s", job_id)
        return True
    except Exception as exc:
        logger.error("Failed to schedule routine reminder: %s", exc)
        return False


def remove_job(job_id: str) -> None:
    scheduler = get_scheduler()
    if scheduler and scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Removed scheduler job: %s", job_id)


def _medicine_reminder_job(user_id: int, medicine_id: int,
                            medicine_name: str, time_str: str) -> None:
    """Called by APScheduler – auto-creates a medicine_log entry."""
    try:
        from utils.helpers import today_str
        from database.connection import execute_write
        scheduled = f"{today_str()} {time_str}"
        execute_write(
            """INSERT OR IGNORE INTO medicine_logs
               (user_id, medicine_id, scheduled_time, status)
               VALUES (?, ?, ?, 'pending')""",
            (user_id, medicine_id, scheduled),
        )
        logger.info("Medicine reminder fired: %s at %s for user %s",
                    medicine_name, time_str, user_id)
    except Exception as exc:
        logger.error("Medicine reminder job error: %s", exc)


def _routine_reminder_job(user_id: int, reminder_id: int,
                           title: str, time_str: str) -> None:
    """Called by APScheduler – auto-creates a reminder_log entry."""
    try:
        from utils.helpers import today_str
        from database.connection import execute_write
        scheduled = f"{today_str()} {time_str}"
        execute_write(
            """INSERT OR IGNORE INTO reminder_logs
               (user_id, reminder_id, scheduled_time, status)
               VALUES (?, ?, ?, 'pending')""",
            (user_id, reminder_id, scheduled),
        )
        logger.info("Routine reminder fired: %s at %s for user %s",
                    title, time_str, user_id)
    except Exception as exc:
        logger.error("Routine reminder job error: %s", exc)


def _day_abbr(day: str) -> str:
    return {
        "monday":    "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday":  "thu", "friday":  "fri", "saturday":  "sat",
        "sunday":    "sun",
    }.get(day.lower(), day[:3].lower())


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down.")
