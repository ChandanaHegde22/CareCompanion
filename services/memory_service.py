"""
services/memory_service.py – AI Long-Term Memory for CareCompanion.
Stores and retrieves personalised facts about the user to enrich AI responses.
"""

import logging
from database.connection import fetch_all, execute_write, fetch_one
from utils.helpers import now_str

logger = logging.getLogger(__name__)

# Memory type constants
MEM_PREFERENCE = "preference"   # food, music, hobbies
MEM_PERSON     = "person"       # family, doctor names
MEM_ROUTINE    = "routine"      # wake up time, walk habits
MEM_MEDICAL    = "medical"      # conditions, allergies, medicines


def store_memory(user_id: int, memory_type: str, key: str, value: str) -> dict:
    """Add or update a memory fact."""
    if not key.strip() or not value.strip():
        return {"success": False, "message": "Key and value are required."}
    execute_write(
        """INSERT INTO user_memory (user_id, memory_type, key, value, updated_at)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(user_id, key) DO UPDATE
           SET value=excluded.value, updated_at=excluded.updated_at""",
        (user_id, memory_type, key.strip().lower(), value.strip(), now_str()),
    )
    logger.info("Memory stored: user=%s key=%s", user_id, key)
    return {"success": True, "message": "Memory saved!"}


def get_memory(user_id: int, key: str = "", memory_type: str = "") -> list[dict]:
    """Retrieve memories optionally filtered by key or type."""
    if key:
        return fetch_all(
            "SELECT * FROM user_memory WHERE user_id=? AND key LIKE ?",
            (user_id, f"%{key.lower()}%"),
        )
    if memory_type:
        return fetch_all(
            "SELECT * FROM user_memory WHERE user_id=? AND memory_type=? ORDER BY key",
            (user_id, memory_type),
        )
    return fetch_all(
        "SELECT * FROM user_memory WHERE user_id=? ORDER BY memory_type, key",
        (user_id,),
    )


def get_all_memories(user_id: int) -> list[dict]:
    return fetch_all(
        "SELECT * FROM user_memory WHERE user_id=? ORDER BY memory_type, key",
        (user_id,),
    )


def delete_memory(user_id: int, memory_id: int) -> dict:
    execute_write(
        "DELETE FROM user_memory WHERE id=? AND user_id=?", (memory_id, user_id)
    )
    return {"success": True, "message": "Memory deleted."}


def format_memories_for_prompt(user_id: int) -> str:
    """
    Build a structured text block of user memories for the AI system prompt.
    Returns an empty string if no memories exist.
    """
    memories = get_all_memories(user_id)
    if not memories:
        return ""

    sections: dict[str, list[str]] = {
        MEM_PERSON:     [],
        MEM_PREFERENCE: [],
        MEM_MEDICAL:    [],
        MEM_ROUTINE:    [],
    }
    for m in memories:
        mt = m.get("memory_type", MEM_PREFERENCE)
        sections.setdefault(mt, []).append(f"  • {m['key']}: {m['value']}")

    labels = {
        MEM_PERSON:     "👨‍👩‍👧 People the user knows",
        MEM_PREFERENCE: "❤️ User preferences",
        MEM_MEDICAL:    "🏥 Medical information",
        MEM_ROUTINE:    "⏰ Daily routines",
    }
    lines = ["── User Memory ──"]
    for mt, items in sections.items():
        if items:
            lines.append(f"\n{labels.get(mt, mt)}:")
            lines.extend(items)
    return "\n".join(lines)


# ── Auto-extraction from conversation ─────────────────────────────────────────

def extract_and_store_memories(user_id: int, text: str) -> None:
    """
    Heuristically detect and store facts mentioned by the user in conversation.
    Runs silently; any errors are logged and ignored.
    """
    try:
        lower = text.lower()
        # Detect family mentions
        _check_person(user_id, lower, "son",        "son's name")
        _check_person(user_id, lower, "daughter",   "daughter's name")
        _check_person(user_id, lower, "wife",       "wife's name")
        _check_person(user_id, lower, "husband",    "husband's name")
        _check_person(user_id, lower, "doctor",     "doctor's name")
        # Detect food preferences
        for food in ["like to eat", "favourite food", "favorite food", "love eating"]:
            if food in lower:
                idx  = lower.index(food) + len(food)
                rest = text[idx: idx + 40].strip()
                if rest:
                    store_memory(user_id, MEM_PREFERENCE, "favourite_food", rest)
    except Exception as exc:
        logger.debug("Memory extraction skipped: %s", exc)


def _check_person(user_id: int, lower: str, role: str, key: str) -> None:
    """Look for 'my <role> is/named/called <name>' patterns."""
    import re
    patterns = [
        rf"my {role}(?:'s name)? is ([A-Z][a-z]+)",
        rf"my {role} named ([A-Z][a-z]+)",
        rf"my {role} called ([A-Z][a-z]+)",
    ]
    for pat in patterns:
        m = re.search(pat, lower, re.IGNORECASE)
        if m:
            store_memory(user_id, MEM_PERSON, key, m.group(1))
            break
