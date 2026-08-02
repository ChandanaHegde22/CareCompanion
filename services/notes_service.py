"""
services/notes_service.py – Personal notes management.
Supports text and voice notes with tagging and full-text search.
"""

import logging
from database.connection import fetch_all, fetch_one, execute_write
from utils.helpers import now_str

logger = logging.getLogger(__name__)


def add_note(user_id: int, content: str, title: str = "",
             note_type: str = "general", tags: str = "") -> dict:
    if not content.strip():
        return {"success": False, "message": "Note content cannot be empty."}
    nid = execute_write(
        """INSERT INTO notes (user_id, title, content, note_type, tags)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, title.strip(), content.strip(), note_type, tags.strip()),
    )
    return {"success": True, "message": "Note saved!", "note_id": nid}


def get_notes(user_id: int, search: str = "",
              note_type: str = "", limit: int = 100) -> list[dict]:
    if search.strip():
        return fetch_all(
            """SELECT * FROM notes
               WHERE user_id=?
                 AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (user_id, f"%{search}%", f"%{search}%", f"%{search}%", limit),
        )
    if note_type:
        return fetch_all(
            "SELECT * FROM notes WHERE user_id=? AND note_type=? ORDER BY updated_at DESC LIMIT ?",
            (user_id, note_type, limit),
        )
    return fetch_all(
        "SELECT * FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
        (user_id, limit),
    )


def get_note(note_id: int) -> dict | None:
    return fetch_one("SELECT * FROM notes WHERE id=?", (note_id,))


def update_note(note_id: int, content: str, title: str = "",
                tags: str = "") -> dict:
    execute_write(
        "UPDATE notes SET title=?, content=?, tags=?, updated_at=? WHERE id=?",
        (title.strip(), content.strip(), tags.strip(), now_str(), note_id),
    )
    return {"success": True, "message": "Note updated!"}


def delete_note(note_id: int) -> dict:
    execute_write("DELETE FROM notes WHERE id=?", (note_id,))
    return {"success": True, "message": "Note deleted."}


def get_notes_count(user_id: int) -> int:
    from database.connection import fetch_one as fo
    row = fo("SELECT COUNT(*) as cnt FROM notes WHERE user_id=?", (user_id,))
    return (row or {}).get("cnt", 0)
