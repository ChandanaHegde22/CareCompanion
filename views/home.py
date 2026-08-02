"""
pages/home.py – CareCompanion Home Dashboard
Shows welcome card, today's summary, quick actions and recent activity.
"""

import streamlit as st
from datetime import datetime

from services.medicine_service  import get_today_medicines, get_adherence_stats
from services.reminder_service  import get_today_reminders, get_completion_stats
from services.mood_service      import get_today_mood, get_mood_statistics
from services.emergency_service import get_emergency_logs
from services.chat_service      import get_conversation_count
from authentication.auth        import get_current_user_id
import config


def render():
    user    = st.session_state.get("user", {})
    user_id = get_current_user_id()
    name    = user.get("full_name") or user.get("username", "Friend")
    hour    = datetime.now().hour
    greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

    # ── Welcome card ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="welcome-card">
        <h1>👋 {greeting}, {name}!</h1>
        <p>How are you feeling today? I'm here to help you with anything you need.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Today's summary metrics ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    # Medicines
    today_meds  = get_today_medicines(user_id)
    taken_count = sum(1 for m in today_meds if m["status"] == "taken")
    total_meds  = len(today_meds)

    # Reminders
    today_rems  = get_today_reminders(user_id)
    done_rems   = sum(1 for r in today_rems if r["status"] == "completed")
    total_rems  = len(today_rems)

    # Mood
    today_mood  = get_today_mood(user_id)
    mood_info   = config.MOODS.get(today_mood["mood"] if today_mood else "neutral", {})
    mood_emoji  = mood_info.get("emoji", "😐")

    # Conversations
    conv_count  = get_conversation_count(user_id)

    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:#6C63FF">
            <div class="metric-value">{taken_count}/{total_meds}</div>
            <div class="metric-label">💊 Medicines Today</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:#43C6AC">
            <div class="metric-value">{done_rems}/{total_rems}</div>
            <div class="metric-label">✅ Tasks Done</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        mood_label = today_mood["mood"].title() if today_mood else "Not logged"
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:#FF6584">
            <div class="metric-value">{mood_emoji}</div>
            <div class="metric-label">🎭 Mood – {mood_label}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color:#FDCB6E">
            <div class="metric-value">{conv_count}</div>
            <div class="metric-label">💬 Total Chats</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────────────────────
    st.markdown("### 🚀 Quick Actions")
    qa_cols = st.columns(5)
    actions = [
        ("💬", "Chat with AI",   "chat"),
        ("💊", "Medicines",      "medicines"),
        ("⏰", "Reminders",      "reminders"),
        ("📋", "Medical Q&A",    "rag"),
        ("🎙️", "Voice",          "voice"),
    ]
    for col, (icon, label, page) in zip(qa_cols, actions):
        with col:
            if st.button(f"{icon}\n{label}", use_container_width=True, key=f"qa_{page}"):
                st.session_state["page"] = page
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two-column layout: medicines + reminders ──────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown("### 💊 Today's Medicines")
        if not today_meds:
            st.info("No medicines scheduled for today.")
        else:
            for med in today_meds[:5]:
                badge_cls = f"badge-{med['status']}"
                st.markdown(f"""
                <div class="info-card" style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;margin-bottom:0.5rem">
                    <div>
                        <strong>{med['name']}</strong><br>
                        <small style="color:#636E72">{med['dosage']} · {med['time_slot']} · {med['meal_timing']}</small>
                    </div>
                    <span class="status-badge {badge_cls}">{med['status'].upper()}</span>
                </div>""", unsafe_allow_html=True)

    with right:
        st.markdown("### ⏰ Today's Reminders")
        if not today_rems:
            st.info("No reminders scheduled for today.")
        else:
            for rem in today_rems[:5]:
                status_icon = "✅" if rem["status"] == "completed" else "⏳"
                st.markdown(f"""
                <div class="info-card" style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;margin-bottom:0.5rem">
                    <div>
                        <strong>{status_icon} {rem['title']}</strong><br>
                        <small style="color:#636E72">{rem['time']} · {rem['reminder_type']}</small>
                    </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Recent emergencies ────────────────────────────────────────────────────
    emergencies = get_emergency_logs(user_id, limit=3)
    if emergencies:
        st.markdown("### 🚨 Recent Emergency Alerts")
        for e in emergencies:
            resolved = "✅ Resolved" if e.get("resolved_at") else "🔴 Active"
            st.markdown(f"""
            <div class="info-card" style="border-left:4px solid #E17055;padding:0.75rem 1rem;margin-bottom:0.5rem">
                <strong>{e['emergency_type'].replace('_',' ').title()}</strong>
                <span style="float:right;font-size:0.8rem">{resolved}</span><br>
                <small style="color:#636E72">{e['created_at'][:16]} · Severity: {e['severity']}</small>
            </div>""", unsafe_allow_html=True)

    # ── Emergency quick-call button ───────────────────────────────────────────
    st.markdown("---")
    if st.button("🆘  EMERGENCY HELP", type="primary", use_container_width=True, key="home_sos"):
        st.session_state["page"] = "emergency"
        st.rerun()
