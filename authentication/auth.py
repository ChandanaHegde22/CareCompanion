"""
authentication/auth.py – CareCompanion Authentication Utilities
Handles password hashing, verification and Streamlit session management.
"""

import logging
import streamlit as st
import bcrypt

logger = logging.getLogger(__name__)


# ── Password Helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt and return the hash string."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* password."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


# ── Session Management ────────────────────────────────────────────────────────

def init_session() -> None:
    """Initialise all session-state keys that the app depends on."""
    defaults = {
        "authenticated": False,
        "user_id":       None,
        "username":      None,
        "user":          None,
        "page":          "home",
        "language":      "en",
        "theme":         "light",
        "chat_history":  [],
        "rag_history":   [],
        "emergency_flag": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def login_session(user: dict) -> None:
    """Populate session state after a successful login."""
    st.session_state["authenticated"] = True
    st.session_state["user_id"]       = user["id"]
    st.session_state["username"]      = user["username"]
    st.session_state["user"]          = user
    st.session_state["language"]      = user.get("language", "en")
    st.session_state["theme"]         = user.get("theme", "light")
    st.session_state["page"]          = "home"
    st.session_state["chat_history"]  = []
    st.session_state["rag_history"]   = []


def logout_session() -> None:
    """Clear all auth-related session state."""
    for key in ("authenticated", "user_id", "username", "user",
                "chat_history", "rag_history", "emergency_flag"):
        st.session_state[key] = None if key not in ("authenticated", "emergency_flag") else False
    st.session_state["page"] = "home"


def require_auth() -> bool:
    """
    Guard function for pages that need authentication.
    Returns True if logged in, else renders a warning and returns False.
    """
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please log in to access this page.")
        st.session_state["page"] = "login"
        return False
    return True


def get_current_user_id() -> int | None:
    return st.session_state.get("user_id")


def get_current_language() -> str:
    return st.session_state.get("language", "en")
