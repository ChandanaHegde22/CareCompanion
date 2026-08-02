"""
pages/chat.py – AI Companion Chat Interface
Full-featured chat with Gemini, conversation history, mood detection and TTS.
"""

import streamlit as st
from datetime import datetime

from services.chat_service   import send_message, get_recent_history, clear_history
from services.mood_service   import analyze_mood, log_mood
from services.memory_service import extract_and_store_memories
from services.emergency_service import log_emergency, notify_emergency_contacts
from speech.tts              import speak_in_streamlit
from authentication.auth     import get_current_user_id, get_current_language
import config


def render():
    user_id  = get_current_user_id()
    language = get_current_language()
    user     = st.session_state.get("user", {})
    name     = user.get("full_name") or user.get("username", "Friend")

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown('<div class="page-title">💬 Chat with CareCompanion</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your caring AI companion — always here for you</div>', unsafe_allow_html=True)

    # ── Initialise session chat history ───────────────────────────────────────
    if "chat_history" not in st.session_state or not isinstance(st.session_state["chat_history"], list):
        st.session_state["chat_history"] = []

    if not st.session_state["chat_history"]:
        db_history = get_recent_history(user_id, limit=10)
        st.session_state["chat_history"] = db_history

    # ── Top toolbar ───────────────────────────────────────────────────────────
    col_lang, col_tts, col_clear = st.columns([2, 1, 1])
    with col_lang:
        lang_opts = {"en": "🇬🇧 English", "hi": "🇮🇳 Hindi", "kn": "🇮🇳 Kannada"}
        selected_lang = st.selectbox(
            "Language", list(lang_opts.keys()),
            format_func=lambda k: lang_opts[k],
            index=list(lang_opts.keys()).index(language),
            key="chat_lang_select",
            label_visibility="collapsed",
        )
        if selected_lang != language:
            st.session_state["language"] = selected_lang
            st.rerun()

    with col_tts:
        enable_tts = st.toggle("🔊 Voice", value=st.session_state.get("chat_tts", False), key="chat_tts")

    with col_clear:
        if st.button("🗑️ Clear", key="clear_chat_btn"):
            clear_history(user_id)
            st.session_state["chat_history"] = []
            st.success("Chat cleared!")
            st.rerun()

    # ── Emergency alert banner ────────────────────────────────────────────────
    if st.session_state.get("emergency_flag"):
        st.markdown("""
        <div class="emergency-banner">
            <h2>🚨 EMERGENCY DETECTED</h2>
            <p>Your emergency contacts are being notified. Please stay calm and call for help!</p>
        </div>""", unsafe_allow_html=True)
        if st.button("✅ I'm Safe Now", key="safe_btn"):
            st.session_state["emergency_flag"] = False
            st.rerun()

    # ── Chat display ──────────────────────────────────────────────────────────
    st.markdown('<div class="chat-container" id="chat-box">', unsafe_allow_html=True)

    history = st.session_state["chat_history"]
    if not history:
        st.markdown(f"""
        <div style="text-align:center;padding:2rem;color:#636E72">
            <div style="font-size:3rem">🤗</div>
            <p style="font-size:1.1rem">Hello {name}! I'm your CareCompanion.<br>
            Feel free to chat with me about anything!</p>
        </div>""", unsafe_allow_html=True)
    else:
        for turn in history:
            ts = str(turn.get("timestamp", ""))[:16]
            st.markdown(f"""
            <div class="chat-bubble-user">{turn['message']}<div class="chat-timestamp">{ts}</div></div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="chat-bubble-ai">🤖 {turn['response']}<div class="chat-timestamp">CareCompanion · {ts}</div></div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Input area ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    # Quick suggestions
    suggestions = [
        "How are you?", "I'm feeling lonely today",
        "Tell me a joke", "I have a headache",
        "Remind me about my medicines", "I can't sleep well",
    ]
    st.markdown("**💡 Quick Messages:**")
    sug_cols = st.columns(3)
    for i, sug in enumerate(suggestions[:6]):
        with sug_cols[i % 3]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state["pending_message"] = sug

    # Text input
    lang_names = {'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada'}
    lang_name = lang_names.get(language, 'English')
    user_input = st.chat_input(
        f"Type your message in {lang_name}…",
        key="chat_input_box",
    )

    # Handle suggestion selection
    if "pending_message" in st.session_state and st.session_state["pending_message"]:
        user_input = st.session_state.pop("pending_message")

    # ── Process message ───────────────────────────────────────────────────────
    if user_input and user_input.strip():
        with st.spinner("💭 Thinking…"):
            result = send_message(
                user_id=user_id,
                message=user_input.strip(),
                language=language,
                session_history=history[-8:],
            )

        if result["success"]:
            # Add to session history
            new_turn = {
                "message":   user_input.strip(),
                "response":  result["response"],
                "language":  language,
                "timestamp": datetime.now().isoformat(),
            }
            st.session_state["chat_history"].append(new_turn)

            # Auto-extract memories
            extract_and_store_memories(user_id, user_input)

            # Mood analysis (background)
            mood_data = analyze_mood(user_input)
            if mood_data and mood_data.get("mood"):
                log_mood(
                    user_id,
                    mood_data["mood"],
                    mood_data["mood_score"],
                    notes=user_input[:200],
                    triggers=mood_data.get("triggers", ""),
                    suggestions=mood_data.get("suggestions", ""),
                )
                if mood_data.get("needs_attention"):
                    st.warning(
                        f"💜 It sounds like you might be feeling {mood_data['mood']}. "
                        "Remember, I'm always here. Would you like to talk about it?"
                    )

            # Emergency handling
            if result.get("is_emergency") and result.get("emergency_data"):
                ed  = result["emergency_data"]
                eid = log_emergency(user_id, user_input, ed["emergency_type"], ed["severity"])
                notify_emergency_contacts(user_id, eid, ed["emergency_type"], user_input)
                st.session_state["emergency_flag"] = True

            # TTS playback
            if enable_tts and result["response"]:
                speak_in_streamlit(result["response"], language)

        else:
            st.error(f"⚠️ {result.get('response', 'Something went wrong.')}")

        st.rerun()
