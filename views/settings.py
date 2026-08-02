"""
pages/settings.py – Application Settings
Language, theme, voice speed, notifications, data export and account deletion.
"""

import streamlit as st
import json
from datetime import datetime

from services.auth_service   import get_settings, update_settings, delete_account
from services.chat_service   import get_conversation_history, clear_history
from services.notes_service  import get_notes
from services.medicine_service import get_medicines
from authentication.auth     import get_current_user_id, logout_session
import config


def render():
    user_id = get_current_user_id()
    settings = get_settings(user_id)

    st.markdown('<div class="page-title">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Customise your CareCompanion experience</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🌐 Language & Display", "🔊 Voice", "🔔 Notifications", "📦 Data & Account"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Language & Display
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("#### 🌐 Language & Display")

        lang_opts  = {"en":"🇬🇧 English","hi":"🇮🇳 Hindi","kn":"🇮🇳 Kannada"}
        cur_lang   = settings.get("language","en")
        sel_lang   = st.selectbox("App Language", list(lang_opts.keys()),
                                   format_func=lambda k: lang_opts[k],
                                   index=list(lang_opts.keys()).index(cur_lang),
                                   key="set_lang")

        theme_opts = {"light":"☀️ Light","dark":"🌙 Dark"}
        cur_theme  = settings.get("theme","light")
        sel_theme  = st.selectbox("Theme", list(theme_opts.keys()),
                                   format_func=lambda k: theme_opts[k],
                                   index=list(theme_opts.keys()).index(cur_theme),
                                   key="set_theme")

        font_opts  = {"small":"Small (14px)","medium":"Medium (16px)","large":"Large (18px)","xlarge":"Extra Large (20px)"}
        cur_font   = settings.get("font_size","medium")
        sel_font   = st.selectbox("Font Size", list(font_opts.keys()),
                                   format_func=lambda k: font_opts[k],
                                   index=list(font_opts.keys()).index(cur_font),
                                   key="set_font")

        if st.button("💾 Save Display Settings", type="primary", key="save_display_btn"):
            res = update_settings(user_id, language=sel_lang, theme=sel_theme, font_size=sel_font)
            if res["success"]:
                st.session_state["language"] = sel_lang
                st.session_state["theme"]    = sel_theme
                st.success(res["message"])
                st.rerun()
            else:
                st.error(res["message"])

        st.markdown("---")
        st.markdown("#### 🎨 Theme Preview")
        if sel_theme == "dark":
            st.markdown("""
            <div style="background:#1A1A2E;border-radius:12px;padding:1rem;color:white">
                <strong style="color:#8B85FF">🌙 Dark Mode Preview</strong><br>
                <span style="color:#E8E8F0">Your app will look like this in dark mode.</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#F5F7FF;border-radius:12px;padding:1rem;border:1px solid #E8EAFF">
                <strong style="color:#6C63FF">☀️ Light Mode Preview</strong><br>
                <span style="color:#2D3436">Clean and calm light theme for easy reading.</span>
            </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – Voice Settings
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### 🔊 Voice & Speech Settings")

        cur_speed = settings.get("voice_speed", 1.0)
        sel_speed = st.slider("Voice Reading Speed", 0.5, 2.0, float(cur_speed), 0.25,
                               format="%.2fx", key="set_speed",
                               help="1.0x = normal speed. Lower for slower speech.")

        cur_vol   = settings.get("reminder_volume", 80)
        sel_vol   = st.slider("Reminder Volume", 0, 100, int(cur_vol), 5,
                               format="%d%%", key="set_vol")

        st.markdown("#### 🎙️ Voice Test")
        test_text = st.text_input("Test message", value="Hello! I am your CareCompanion. How are you today?",
                                   key="voice_test_input")
        test_lang = st.session_state.get("language","en")
        if st.button("▶ Play Test", key="play_test_btn"):
            from speech.tts import speak_in_streamlit
            speak_in_streamlit(test_text, test_lang)

        if st.button("💾 Save Voice Settings", type="primary", key="save_voice_btn"):
            res = update_settings(user_id, voice_speed=sel_speed, reminder_volume=sel_vol)
            if res["success"]:
                st.success(res["message"])
            else:
                st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Notifications
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### 🔔 Notification Preferences")

        cur_notif = bool(settings.get("notifications_enabled", 1))
        sel_notif = st.toggle("Enable Notifications", value=cur_notif, key="set_notif")

        st.markdown("---")
        st.markdown("""
        <div class="cc-info-box">
            <strong>Notification Types:</strong><br>
            • 💊 Medicine reminders<br>
            • ⏰ Daily task reminders<br>
            • 🎭 Mood check-in reminders<br>
            • 🚨 Emergency alerts (always active)
        </div>""", unsafe_allow_html=True)

        if st.button("💾 Save Notification Settings", type="primary", key="save_notif_btn"):
            res = update_settings(user_id, notifications_enabled=1 if sel_notif else 0)
            if res["success"]:
                st.success(res["message"])
            else:
                st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 – Data & Account
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("#### 📦 Export Your Data")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            if st.button("📥 Export Conversations", use_container_width=True, key="exp_conv"):
                convs = get_conversation_history(user_id, days=365)
                data  = json.dumps(convs, indent=2, default=str)
                st.download_button(
                    "⬇ Download JSON",
                    data=data,
                    file_name=f"carecompanion_chats_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    key="dl_conv",
                )

        with col_exp2:
            if st.button("📥 Export Notes", use_container_width=True, key="exp_notes"):
                notes = get_notes(user_id)
                data  = json.dumps(notes, indent=2, default=str)
                st.download_button(
                    "⬇ Download JSON",
                    data=data,
                    file_name=f"carecompanion_notes_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    key="dl_notes",
                )

        st.markdown("---")
        st.markdown("#### 🧹 Clear Data")

        if st.button("🗑️ Clear All Conversations", type="secondary", key="clear_conv_btn"):
            if st.session_state.get("confirm_clear_conv"):
                clear_history(user_id)
                st.session_state["chat_history"] = []
                st.session_state["confirm_clear_conv"] = False
                st.success("Conversation history cleared.")
            else:
                st.session_state["confirm_clear_conv"] = True
                st.warning("⚠️ Click again to confirm clearing all conversations.")

        st.markdown("---")
        st.markdown("#### ❗ Danger Zone")

        with st.expander("🗑️ Delete My Account", expanded=False):
            st.error("""
            **Warning:** This action is permanent and cannot be undone.
            All your data — conversations, medicines, reminders, notes, and emergency logs — will be deleted.
            """)
            confirm_text = st.text_input("Type 'DELETE MY ACCOUNT' to confirm:",
                                          key="del_account_confirm")
            if st.button("🗑️ Permanently Delete Account", type="primary", key="del_account_btn"):
                if confirm_text == "DELETE MY ACCOUNT":
                    delete_account(user_id)
                    logout_session()
                    st.success("Account deleted. Goodbye!")
                    st.session_state["page"] = "login"
                    st.rerun()
                else:
                    st.error("Confirmation text doesn't match. Account not deleted.")
