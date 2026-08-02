"""
pages/emergency.py – Emergency Detection & Alert System
Detects emergencies from text/voice, sends SMS/email, logs incidents.
"""

import streamlit as st
from datetime import datetime

from services.emergency_service import (
    log_emergency, notify_emergency_contacts,
    get_emergency_logs, resolve_emergency, get_emergency_stats,
)
from services.auth_service import get_emergency_contacts, add_emergency_contact, delete_emergency_contact
from utils.emergency_detector import detect_emergency, get_emergency_message, SEVERITY_MAP
from authentication.auth import get_current_user_id
from utils.helpers import severity_emoji, format_datetime
import config


def render():
    user_id = get_current_user_id()
    user    = st.session_state.get("user", {})
    name    = user.get("full_name") or user.get("username","Friend")

    st.markdown('<div class="page-title">🚨 Emergency Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your safety is our top priority</div>', unsafe_allow_html=True)

    # ── Emergency SOS – always visible ───────────────────────────────────────
    st.markdown("""
    <div class="emergency-banner">
        <h2>🆘 In an Emergency?</h2>
        <p>Press the button below or describe your situation. Help will be notified immediately.</p>
    </div>""", unsafe_allow_html=True)

    sos_cols = st.columns(3)
    with sos_cols[0]:
        if st.button("🫀 Chest Pain / Heart Attack", type="primary",
                     use_container_width=True, key="sos_cardiac"):
            _trigger_emergency(user_id, name, "I have severe chest pain", "cardiac", "critical")
    with sos_cols[1]:
        if st.button("🫁 Can't Breathe", type="primary",
                     use_container_width=True, key="sos_breath"):
            _trigger_emergency(user_id, name, "I can't breathe", "breathing", "critical")
    with sos_cols[2]:
        if st.button("🤕 I Fell Down", type="primary",
                     use_container_width=True, key="sos_fall"):
            _trigger_emergency(user_id, name, "I fell down", "fall", "medium")

    sos_cols2 = st.columns(3)
    with sos_cols2[0]:
        if st.button("🧠 Stroke / Paralysis", type="primary",
                     use_container_width=True, key="sos_stroke"):
            _trigger_emergency(user_id, name, "I think I'm having a stroke", "stroke", "critical")
    with sos_cols2[1]:
        if st.button("😰 Severe Pain", type="primary",
                     use_container_width=True, key="sos_pain"):
            _trigger_emergency(user_id, name, "I have severe unbearable pain", "severe_pain", "high")
    with sos_cols2[2]:
        if st.button("🆘 General Emergency", type="primary",
                     use_container_width=True, key="sos_general"):
            _trigger_emergency(user_id, name, "Emergency! I need help", "general", "high")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["💬 Describe Situation", "📋 Emergency History", "📞 Emergency Contacts"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Describe situation
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown("#### 📝 Describe Your Situation")
        st.markdown("Type what is happening. The AI will detect if it's an emergency and alert your contacts.")

        situation = st.text_area(
            "What is happening?",
            height=110,
            placeholder="e.g. 'I fell in the bathroom and can't get up' / 'I have chest pain that is spreading to my arm'",
            key="em_situation_input",
            label_visibility="collapsed",
        )
        if st.button("🔍 Check & Alert", type="primary", use_container_width=True, key="em_check_btn"):
            if situation.strip():
                result = detect_emergency(situation)
                if result["is_emergency"]:
                    eid = log_emergency(user_id, situation, result["emergency_type"], result["severity"])
                    notif = notify_emergency_contacts(user_id, eid, result["emergency_type"], situation)
                    msg   = get_emergency_message(result["emergency_type"])
                    st.markdown(f"""
                    <div class="emergency-banner">
                        <h2>{severity_emoji(result['severity'])} EMERGENCY DETECTED</h2>
                        <p>{msg}</p>
                        <p><strong>Contacts notified:</strong> {', '.join(notif['contacts']) or 'None configured'}</p>
                        <p><strong>SMS sent:</strong> {notif['sms_sent']} · <strong>Emails sent:</strong> {notif['email_sent']}</p>
                    </div>""", unsafe_allow_html=True)
                    st.session_state["emergency_flag"] = True
                    st.info("📞 If this is a life-threatening emergency, please also call local emergency services (108 / 911 / 999)!")
                else:
                    st.success(f"""
                    ✅ No emergency detected in your message.
                    **Matched keywords:** {', '.join(result['matched_keywords']) or 'None'}

                    If you feel unwell, please use the quick buttons above or call a loved one.
                    """)
            else:
                st.warning("Please describe your situation.")

        # Emergency guidelines
        with st.expander("📋 What to do in an emergency"):
            st.markdown("""
            ### 🆘 Immediate Steps
            1. **Stay calm** – take slow, deep breaths
            2. **Don't move** if you've fallen or have a possible injury
            3. **Call for help** – shout for someone nearby
            4. **Press the SOS buttons** above to alert your emergency contacts
            5. **Call emergency services** – 108 (India) / 911 (US) / 999 (UK)

            ### ❤️ Heart Attack Signs
            - Chest pain or pressure spreading to arm/jaw
            - Shortness of breath, sweating, nausea
            → **Call 108/911 immediately**

            ### 🧠 Stroke Signs (FAST)
            - **F**ace drooping · **A**rm weakness · **S**peech slurred · **T**ime to call!
            → **Call 108/911 immediately**
            """)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – Emergency History
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        logs  = get_emergency_logs(user_id, limit=20)
        stats = get_emergency_stats(user_id)

        if stats["total"] > 0:
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Incidents", stats["total"])
            k2.metric("Most Common", list(stats["by_type"].keys())[0].replace("_"," ").title()
                      if stats["by_type"] else "—")
            k3.metric("Avg per Week", stats["avg_per_week"])

        if not logs:
            st.success("🎉 No emergency incidents recorded. Stay safe!")
        else:
            st.markdown(f"**{len(logs)} emergency record(s):**")
            for log in logs:
                sev_e     = severity_emoji(log["severity"])
                resolved  = bool(log.get("resolved_at"))
                status_lbl = "✅ Resolved" if resolved else "🔴 Unresolved"

                with st.expander(
                    f"{sev_e} {log['emergency_type'].replace('_',' ').title()} – {str(log['created_at'])[:16]}",
                    expanded=False,
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Status:** {status_lbl}")
                        st.markdown(f"**Severity:** {log['severity'].title()}")
                        st.markdown(f"**Trigger:** _{log['trigger_text'][:120]}_")
                    with c2:
                        st.markdown(f"**Contacts Notified:** {log.get('contacts_notified','—')}")
                        st.markdown(f"**Actions:** {log.get('actions_taken','—')}")
                        if log.get("resolved_at"):
                            st.markdown(f"**Resolved:** {str(log['resolved_at'])[:16]}")

                    if not resolved:
                        if st.button("✅ Mark Resolved", key=f"resolve_{log['id']}", type="secondary"):
                            resolve_emergency(log["id"])
                            st.success("Marked as resolved.")
                            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Emergency Contacts
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        contacts = get_emergency_contacts(user_id)
        st.markdown(f"#### 📞 Your Emergency Contacts ({len(contacts)})")

        if not contacts:
            st.warning("⚠️ No emergency contacts added. Add someone who can be alerted when an emergency is detected.")
        else:
            for c in contacts:
                col_inf, col_del = st.columns([5, 1])
                with col_inf:
                    st.markdown(f"""
                    <div class="info-card" style="padding:0.65rem 1rem;margin-bottom:0.4rem">
                        <strong>👤 {c['name']}</strong>
                        {f" · {c['relationship']}" if c.get('relationship') else ''}
                        <br>
                        📱 {c.get('phone','—')}
                        {f" · ✉️ {c['email']}" if c.get('email') else ''}
                    </div>""", unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_contact_{c['id']}", help="Remove contact"):
                        delete_emergency_contact(c["id"])
                        st.rerun()

        st.markdown("---")
        st.markdown("#### ➕ Add Emergency Contact")
        with st.form("add_contact_form", clear_on_submit=True):
            fc1, fc2 = st.columns(2)
            c_name   = fc1.text_input("Full Name *", placeholder="Dr. Priya Sharma")
            c_rel    = fc2.text_input("Relationship", placeholder="Daughter / Doctor")
            fc3, fc4 = st.columns(2)
            c_phone  = fc3.text_input("Phone Number *", placeholder="+91 98765 43210")
            c_email  = fc4.text_input("Email (optional)", placeholder="email@example.com")
            if st.form_submit_button("➕ Add Contact", type="primary", use_container_width=True):
                res = add_emergency_contact(user_id, c_name, c_rel, c_phone, c_email)
                if res["success"]:
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])


# ── Helper ────────────────────────────────────────────────────────────────────
def _trigger_emergency(user_id: int, user_name: str, trigger: str,
                        etype: str, severity: str) -> None:
    eid   = log_emergency(user_id, trigger, etype, severity)
    notif = notify_emergency_contacts(user_id, eid, etype, trigger)
    msg   = get_emergency_message(etype)
    st.markdown(f"""
    <div class="emergency-banner">
        <h2>🚨 EMERGENCY ALERT SENT</h2>
        <p>{msg}</p>
        <p>Contacts notified: {', '.join(notif['contacts']) or 'None configured'}</p>
    </div>""", unsafe_allow_html=True)
    st.session_state["emergency_flag"] = True
    st.info("📞 Please also call: **108** (India) / **911** (US) / **999** (UK) for immediate help.")
