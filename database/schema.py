"""
database/schema.py – CareCompanion Database Schema
All CREATE TABLE statements, indexes, and the initialiser function.
Call ``init_db()`` once at app startup.
"""

import logging
from database.connection import get_db

logger = logging.getLogger(__name__)

# ── DDL Statements ────────────────────────────────────────────────────────────

_DDL = """
-- Users -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    email         TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    full_name     TEXT,
    age           INTEGER,
    phone         TEXT,
    language      TEXT    DEFAULT 'en',
    theme         TEXT    DEFAULT 'light',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP,
    is_active     INTEGER DEFAULT 1
);

-- Emergency contacts ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    relationship TEXT,
    phone        TEXT    NOT NULL,
    email        TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Medicines -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medicines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    dosage       TEXT    NOT NULL,
    frequency    TEXT    NOT NULL,
    times        TEXT    NOT NULL,       -- JSON: ["08:00","20:00"]
    meal_timing  TEXT    DEFAULT 'anytime',
    start_date   TEXT,
    end_date     TEXT,
    notes        TEXT,
    is_active    INTEGER DEFAULT 1,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Medicine adherence logs -----------------------------------------------------
CREATE TABLE IF NOT EXISTS medicine_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    medicine_id    INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    taken_time     TIMESTAMP,
    status         TEXT DEFAULT 'pending',  -- taken | missed | skipped
    notes          TEXT,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- Reminders ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reminders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    title         TEXT    NOT NULL,
    description   TEXT,
    reminder_type TEXT    DEFAULT 'General',
    time          TEXT    NOT NULL,         -- "HH:MM"
    days          TEXT    NOT NULL,         -- JSON: ["monday","wednesday"]
    is_active     INTEGER DEFAULT 1,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Reminder logs ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reminder_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL,
    reminder_id    INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    completed_time TIMESTAMP,
    status         TEXT DEFAULT 'pending',  -- completed | missed
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (reminder_id) REFERENCES reminders(id) ON DELETE CASCADE
);

-- Mood logs -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mood_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    mood        TEXT    NOT NULL,
    mood_score  INTEGER NOT NULL,
    notes       TEXT,
    triggers    TEXT,
    suggestions TEXT,
    logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Conversations ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL,
    message   TEXT    NOT NULL,
    response  TEXT    NOT NULL,
    language  TEXT    DEFAULT 'en',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Uploaded documents ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    filename      TEXT    NOT NULL,
    file_type     TEXT    NOT NULL,
    file_path     TEXT    NOT NULL,
    document_type TEXT,
    chunks_count  INTEGER DEFAULT 0,
    is_indexed    INTEGER DEFAULT 0,
    uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Emergency logs --------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emergency_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,
    trigger_text       TEXT    NOT NULL,
    emergency_type     TEXT    NOT NULL,
    severity           TEXT    DEFAULT 'high',
    contacts_notified  TEXT,               -- JSON list
    actions_taken      TEXT,
    resolved_at        TIMESTAMP,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- AI long-term memory ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_memory (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    memory_type TEXT    NOT NULL,       -- preference | person | routine | medical
    key         TEXT    NOT NULL,
    value       TEXT    NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Notes -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT,
    content    TEXT    NOT NULL,
    note_type  TEXT    DEFAULT 'general',  -- health | personal | voice
    tags       TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Caregivers ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS caregivers (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,   -- elderly user
    caregiver_username TEXT    NOT NULL,
    permission_level   TEXT    DEFAULT 'view',
    added_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User settings ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_settings (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id               INTEGER UNIQUE NOT NULL,
    language              TEXT    DEFAULT 'en',
    voice_speed           REAL    DEFAULT 1.0,
    reminder_volume       INTEGER DEFAULT 80,
    theme                 TEXT    DEFAULT 'light',
    font_size             TEXT    DEFAULT 'medium',
    notifications_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_medicines_user       ON medicines(user_id);
CREATE INDEX IF NOT EXISTS idx_medicine_logs_user   ON medicine_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user       ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_mood_logs_user       ON mood_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user   ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user       ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_emergency_logs_user  ON emergency_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memory_user     ON user_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_user           ON notes(user_id);
"""


import streamlit as st

@st.cache_resource
def init_db() -> None:
    """
    Initialize the SQLite database.
    Creates all tables and indexes if they don't already exist.
    Safe to call multiple times (idempotent).
    """
    try:
        with get_db() as conn:
            conn.executescript(_DDL)
        logger.info("Database initialised successfully.")
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc, exc_info=True)
        raise
