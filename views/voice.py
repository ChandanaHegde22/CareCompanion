"""
pages/voice.py – Voice Assistant
Push-to-talk STT → AI reply → TTS playback. Multilingual support.
"""

import streamlit as st
from datetime import datetime

from services.chat_service      import send_message, get_recent_history
from services.emergency_service import log_emergency, notify_emergency_contacts
from services.mood_service      import analyze_mood, log_mood
from speech.stt                 import audio_bytes_to_text, is_stt_available
from speech.tts                 import speak_in_streamlit, text_to_speech_bytes
from authentication.auth        import get_current_user_id, get_current_language
import config

LANG_NAMES = {"en": "English", "hi": "Hindi", "kn": "Kannada"}


def render():
    user_id  = get_current_user_id()
    language = get_current_language()

    st.markdown('<div class="page-title">🎙️ Voice Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Speak naturally — your companion listens and responds</div>',
                unsafe_allow_html=True)

    # ── Language selector ─────────────────────────────────────────────────────
    lang_col, tts_col = st.columns([2, 2])
    with lang_col:
        lang_opts = {"en": "🇬🇧 English", "hi": "🇮🇳 Hindi", "kn": "🇮🇳 Kannada"}
        sel_lang  = st.selectbox("Language", list(lang_opts.keys()),
                                 format_func=lambda k: lang_opts[k],
                                 index=list(lang_opts.keys()).index(language),
                                 key="voice_lang_select")
        if sel_lang != language:
            st.session_state["language"] = sel_lang
            st.rerun()
    with tts_col:
        voice_speed = st.select_slider("Speech Speed", options=["Slow", "Normal"],
                                       value="Normal", key="voice_speed_slider")

    st.markdown("---")

    # ── Capability check ─────────────────────────────────────────────────────
    stt_ok = is_stt_available()
    if not stt_ok:
        st.warning("⚠️ SpeechRecognition library is not installed. Voice input is unavailable. "
                   "You can still use text input below and listen to AI responses.")

    # ── Push-to-talk ─────────────────────────────────────────────────────────
    st.markdown("### 🎤 Push to Talk")
    st.markdown("""
    <div class="cc-info-box">
        Click the microphone below, speak your message, then stop recording.
        The AI will respond in text <strong>and</strong> voice!
    </div>""", unsafe_allow_html=True)

    recognized_text = ""

    if stt_ok:
        try:
            from audio_recorder_streamlit import audio_recorder
            audio_bytes = audio_recorder(
                text="", recording_color="#E17055", neutral_color="#6C63FF",
                icon_name="microphone", icon_size="3x", key="voice_recorder",
                pause_threshold=2.5,
            )
            if audio_bytes and len(audio_bytes) > 1000:
                with st.spinner("🔄 Transcribing your speech…"):
                    stt_result = audio_bytes_to_text(audio_bytes, language)
                if stt_result["success"]:
                    recognized_text = stt_result["text"]
                    st.markdown(f"""
                    <div class="info-card" style="border-left:4px solid #43C6AC">
                        <strong>🗣️ You said:</strong> {recognized_text}
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning(f"🔇 {stt_result['error']}")
        except ImportError:
            st.warning("audio-recorder-streamlit not installed. Using text input below.")

    # ── Text fallback input ───────────────────────────────────────────────────
    st.markdown("### ⌨️ Or Type Your Message")
    text_input = st.text_input("Type here and press Enter…",
                               placeholder="Hello! How are you? / नमस्ते! / ನಮಸ್ಕಾರ!",
                               key="voice_text_input", label_visibility="collapsed")

    # ── Send button / auto-send from STT ─────────────────────────────────────
    send_via_text   = st.button("💬 Send Message", type="primary",
                                use_container_width=True, key="voice_send_btn")
    final_message   = recognized_text or (text_input.strip() if send_via_text else "")

    if final_message:
        with st.spinner("🤔 CareCompanion is thinking…"):
            history = get_recent_history(user_id, limit=6)
            result  = send_message(user_id, final_message, language=language,
                                   session_history=history)

        if result["success"]:
            response = result["response"]
            st.markdown(f"""
            <div class="chat-bubble-ai" style="max-width:100%;margin:0.5rem 0">
                🤖 {response}
            </div>""", unsafe_allow_html=True)

            # ── Voice playback ────────────────────────────────────────────────
            st.markdown("**🔊 Listen to response:**")
            slow = (voice_speed == "Slow")
            speak_in_streamlit(response, language)

            # Emergency check
            if result.get("is_emergency") and result.get("emergency_data"):
                ed  = result["emergency_data"]
                eid = log_emergency(user_id, final_message, ed["emergency_type"], ed["severity"])
                notify_emergency_contacts(user_id, eid, ed["emergency_type"], final_message)
                st.session_state["emergency_flag"] = True
                st.markdown("""
                <div class="emergency-banner">
                    <h2>🚨 EMERGENCY DETECTED</h2>
                    <p>Your emergency contacts are being notified. Please stay calm!</p>
                </div>""", unsafe_allow_html=True)

            # Mood analysis
            mood_data = analyze_mood(final_message)
            if mood_data and mood_data.get("mood"):
                log_mood(user_id, mood_data["mood"], mood_data["mood_score"],
                         notes=final_message[:200],
                         triggers=mood_data.get("triggers",""),
                         suggestions=mood_data.get("suggestions",""))
        else:
            st.error(f"⚠️ {result.get('response','Something went wrong.')}")

    # ── Conversation history ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📜 Recent Voice Conversations")
    history = get_recent_history(user_id, limit=5)
    if not history:
        st.info("No conversations yet. Start talking!")
    else:
        for turn in history[:5]:
            ts = str(turn.get("timestamp",""))[:16]
            st.markdown(f"""
            <div style="margin-bottom:0.75rem">
                <div class="chat-bubble-user" style="max-width:100%">🙋 {turn['message']}
                    <div class="chat-timestamp">{ts}</div></div>
                <div class="chat-bubble-ai" style="max-width:100%">🤖 {turn['response'][:200]}{'…' if len(turn['response'])>200 else ''}
                    <div class="chat-timestamp">CareCompanion</div></div>
            </div>""", unsafe_allow_html=True)

            # Re-play TTS for history item
            if st.button(f"🔊 Play", key=f"play_hist_{turn.get('timestamp','')}", help="Listen to this response"):
                speak_in_streamlit(turn["response"], language)
