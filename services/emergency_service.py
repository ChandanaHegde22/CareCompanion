"""
services/emergency_service.py – Emergency handling, alerting and logging.
"""

import logging
from datetime import datetime

import config
from database.connection import fetch_all, execute_write, fetch_one
from services.auth_service import get_emergency_contacts
from utils.helpers import to_json, now_str
from utils.emergency_detector import detect_emergency, get_emergency_message

logger = logging.getLogger(__name__)


# ── Emergency Log ─────────────────────────────────────────────────────────────

def log_emergency(user_id: int, trigger_text: str,
                  emergency_type: str, severity: str) -> int:
    """Save an emergency event to the database and return its id."""
    eid = execute_write(
        """INSERT INTO emergency_logs
           (user_id, trigger_text, emergency_type, severity, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, trigger_text, emergency_type, severity, now_str()),
    )
    logger.warning(
        "Emergency logged: id=%s user=%s type=%s severity=%s",
        eid, user_id, emergency_type, severity,
    )
    return eid


def resolve_emergency(emergency_id: int) -> None:
    execute_write(
        "UPDATE emergency_logs SET resolved_at=? WHERE id=?",
        (now_str(), emergency_id),
    )


def get_emergency_logs(user_id: int, limit: int = 50) -> list[dict]:
    return fetch_all(
        """SELECT * FROM emergency_logs
           WHERE user_id=?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    )


# ── Notification ──────────────────────────────────────────────────────────────

def notify_emergency_contacts(user_id: int, emergency_id: int,
                               emergency_type: str, trigger_text: str) -> dict:
    """
    Send SMS and/or email alerts to all emergency contacts.
    Returns a summary of notifications sent.
    """
    contacts = get_emergency_contacts(user_id)
    if not contacts:
        logger.warning("No emergency contacts found for user %s", user_id)
        return {"sms_sent": 0, "email_sent": 0, "contacts": []}

    user = fetch_one("SELECT full_name, username FROM users WHERE id=?", (user_id,))
    user_name = (user or {}).get("full_name") or (user or {}).get("username", "Your loved one")
    message   = get_emergency_message(emergency_type)
    alert_msg = (
        f"🚨 EMERGENCY ALERT – {user_name}\n\n"
        f"{message}\n\n"
        f"Message: '{trigger_text[:100]}'\n"
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "Please respond immediately or call emergency services."
    )

    sms_sent   = 0
    email_sent = 0
    notified   = []

    for contact in contacts:
        # ── SMS via Twilio ────────────────────────────────────────────────────
        if contact.get("phone") and config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            sms_ok = _send_sms(contact["phone"], alert_msg)
            if sms_ok:
                sms_sent += 1

        # ── Email via SendGrid ────────────────────────────────────────────────
        if contact.get("email") and config.SENDGRID_API_KEY:
            email_ok = _send_email(contact["email"], contact["name"],
                                   f"🚨 Emergency Alert – {user_name}", alert_msg)
            if email_ok:
                email_sent += 1

        notified.append(contact["name"])

    # Update emergency log
    execute_write(
        "UPDATE emergency_logs SET contacts_notified=?, actions_taken=? WHERE id=?",
        (to_json(notified),
         f"SMS sent: {sms_sent}, Email sent: {email_sent}",
         emergency_id),
    )

    logger.info("Emergency notifications: sms=%s email=%s", sms_sent, email_sent)
    return {"sms_sent": sms_sent, "email_sent": email_sent, "contacts": notified}


def _send_sms(phone: str, message: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=config.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        logger.info("SMS sent to %s", phone)
        return True
    except Exception as exc:
        logger.error("SMS failed to %s: %s", phone, exc)
        return False


def _send_email(to_email: str, to_name: str, subject: str, body: str) -> bool:
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg   = sendgrid.SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
        mail = Mail(
            from_email=config.FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        sg.send(mail)
        logger.info("Email sent to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Email failed to %s: %s", to_email, exc)
        return False


# ── Stats ────────────────────────────────────────────────────────────────────

def get_emergency_stats(user_id: int) -> dict:
    logs = get_emergency_logs(user_id, limit=100)
    if not logs:
        return {"total": 0, "by_type": {}, "avg_per_week": 0}
    by_type: dict[str, int] = {}
    for log in logs:
        t = log["emergency_type"]
        by_type[t] = by_type.get(t, 0) + 1
    return {"total": len(logs), "by_type": by_type, "avg_per_week": round(len(logs) / 4, 1)}
