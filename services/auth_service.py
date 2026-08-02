"""
services/auth_service.py – User authentication and profile management.
"""

import logging
from datetime import datetime

from authentication.auth import hash_password, verify_password
from database.connection import fetch_one, fetch_all, execute_write, get_db
from utils.validators import validate_email, validate_password, validate_phone

logger = logging.getLogger(__name__)


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str,
                  full_name: str = "", age: int = 0, phone: str = "") -> dict:
    """
    Register a new user.
    Returns {"success": bool, "message": str, "user_id": int | None}.
    """
    username = username.strip().lower()
    email    = email.strip().lower()

    # ── Validation ──────────────────────────────────────────────────────────
    if not username or len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters.", "user_id": None}
    if not validate_email(email):
        return {"success": False, "message": "Invalid email address.", "user_id": None}
    if not validate_password(password):
        return {"success": False, "message": "Password must be at least 8 characters.", "user_id": None}

    # ── Duplicate check ──────────────────────────────────────────────────────
    existing = fetch_one(
        "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
    )
    if existing:
        return {"success": False, "message": "Username or email already registered.", "user_id": None}

    # ── Insert ───────────────────────────────────────────────────────────────
    pw_hash  = hash_password(password)
    user_id  = execute_write(
        """INSERT INTO users (username, email, password_hash, full_name, age, phone)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (username, email, pw_hash, full_name.strip(), age or None, phone.strip() or None),
    )

    # ── Default settings ─────────────────────────────────────────────────────
    execute_write(
        "INSERT INTO user_settings (user_id) VALUES (?)", (user_id,)
    )

    logger.info("New user registered: %s (id=%s)", username, user_id)
    return {"success": True, "message": "Registration successful!", "user_id": user_id}


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(username: str, password: str) -> dict:
    """
    Verify credentials and return user dict on success.
    Returns {"success": bool, "message": str, "user": dict | None}.
    """
    username = username.strip().lower()
    user = fetch_one(
        "SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1",
        (username, username),
    )
    if not user:
        return {"success": False, "message": "User not found.", "user": None}

    if not verify_password(password, user["password_hash"]):
        return {"success": False, "message": "Incorrect password.", "user": None}

    # Update last_login
    execute_write(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.now().isoformat(), user["id"]),
    )
    logger.info("User logged in: %s", username)
    return {"success": True, "message": "Login successful!", "user": dict(user)}


# ── Profile ───────────────────────────────────────────────────────────────────

def get_user(user_id: int) -> dict | None:
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def update_profile(user_id: int, full_name: str = "", age: int = 0,
                   phone: str = "", language: str = "en", theme: str = "light") -> dict:
    """Update user profile fields."""
    if phone and not validate_phone(phone):
        return {"success": False, "message": "Invalid phone number."}
    execute_write(
        """UPDATE users SET full_name=?, age=?, phone=?, language=?, theme=?
           WHERE id=?""",
        (full_name.strip(), age or None, phone.strip() or None, language, theme, user_id),
    )
    return {"success": True, "message": "Profile updated successfully!"}


def change_password(user_id: int, old_password: str, new_password: str) -> dict:
    """Change a user's password after verifying the old one."""
    user = fetch_one("SELECT password_hash FROM users WHERE id=?", (user_id,))
    if not user or not verify_password(old_password, user["password_hash"]):
        return {"success": False, "message": "Current password is incorrect."}
    if not validate_password(new_password):
        return {"success": False, "message": "New password must be at least 8 characters."}
    execute_write(
        "UPDATE users SET password_hash=? WHERE id=?",
        (hash_password(new_password), user_id),
    )
    return {"success": True, "message": "Password changed successfully!"}


def delete_account(user_id: int) -> dict:
    """Soft-delete a user account."""
    execute_write("UPDATE users SET is_active=0 WHERE id=?", (user_id,))
    return {"success": True, "message": "Account deleted."}


# ── Emergency Contacts ────────────────────────────────────────────────────────

def get_emergency_contacts(user_id: int) -> list[dict]:
    return fetch_all(
        "SELECT * FROM emergency_contacts WHERE user_id=? ORDER BY id", (user_id,)
    )


def add_emergency_contact(user_id: int, name: str, relationship: str,
                          phone: str, email: str = "") -> dict:
    if not name.strip():
        return {"success": False, "message": "Contact name is required."}
    if not phone.strip():
        return {"success": False, "message": "Phone number is required."}
    execute_write(
        """INSERT INTO emergency_contacts (user_id, name, relationship, phone, email)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, name.strip(), relationship.strip(), phone.strip(), email.strip()),
    )
    return {"success": True, "message": f"Emergency contact '{name}' added!"}


def update_emergency_contact(contact_id: int, name: str, relationship: str,
                              phone: str, email: str = "") -> dict:
    execute_write(
        "UPDATE emergency_contacts SET name=?, relationship=?, phone=?, email=? WHERE id=?",
        (name.strip(), relationship.strip(), phone.strip(), email.strip(), contact_id),
    )
    return {"success": True, "message": "Contact updated!"}


def delete_emergency_contact(contact_id: int) -> dict:
    execute_write("DELETE FROM emergency_contacts WHERE id=?", (contact_id,))
    return {"success": True, "message": "Contact removed."}


# ── Settings ──────────────────────────────────────────────────────────────────

def get_settings(user_id: int) -> dict:
    settings = fetch_one("SELECT * FROM user_settings WHERE user_id=?", (user_id,))
    if not settings:
        execute_write("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
        settings = fetch_one("SELECT * FROM user_settings WHERE user_id=?", (user_id,))
    return dict(settings) if settings else {}


def update_settings(user_id: int, **kwargs) -> dict:
    allowed = {"language", "voice_speed", "reminder_volume",
               "theme", "font_size", "notifications_enabled"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return {"success": False, "message": "Nothing to update."}
    set_clause = ", ".join(f"{k}=?" for k in updates)
    execute_write(
        f"UPDATE user_settings SET {set_clause} WHERE user_id=?",
        (*updates.values(), user_id),
    )
    # Mirror language/theme on users table as well
    if "language" in updates:
        execute_write("UPDATE users SET language=? WHERE id=?",
                      (updates["language"], user_id))
    if "theme" in updates:
        execute_write("UPDATE users SET theme=? WHERE id=?",
                      (updates["theme"], user_id))
    return {"success": True, "message": "Settings saved!"}
