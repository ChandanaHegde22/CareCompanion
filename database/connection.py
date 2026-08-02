"""
database/connection.py – SQLite connection manager
Provides a thread-safe, context-managed database connection.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path

import config

logger = logging.getLogger(__name__)


def dict_row_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    """Convert a SQLite row into a plain dictionary."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_db():
    """
    Yield a SQLite connection with auto-commit / rollback and proper cleanup.

    Usage::

        with get_db() as conn:
            conn.execute("INSERT INTO users ...")
    """
    conn: sqlite3.Connection | None = None
    try:
        Path(config.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            config.DATABASE_PATH,
            check_same_thread=False,
        )
        conn.row_factory = dict_row_factory
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    except Exception as exc:
        if conn:
            conn.rollback()
        logger.error("Database error: %s", exc, exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """Execute a SELECT and return the first row as a dict (or None)."""
    with get_db() as conn:
        row = conn.execute(sql, params).fetchone()
    return row


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a SELECT and return all rows as a list of dicts."""
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows or []


def execute_write(sql: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid."""
    with get_db() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def execute_many(sql: str, params_list: list[tuple]) -> None:
    """Execute a batch INSERT/UPDATE."""
    with get_db() as conn:
        conn.executemany(sql, params_list)
