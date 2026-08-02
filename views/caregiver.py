"""
pages/caregiver.py – Caregiver Dashboard
Aggregated view of medicine adherence, mood, emergencies and reminders.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from services.caregiver_service import (
    get_dashboard_data, add_caregiver, get_caregivers,
    remove_caregiver, get_linked_patients,
)
from authentication.auth import get_current_user_id
import config


def render():
    user_id  = get_current_user_id()
    username = st.session_state.get("username","")

    st.markdown('<div class="page-title">👥 Caregiver Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Monitor health and safety of your loved ones</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 My Health Summary", "👴 View Patient", "🔗 Manage Access"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Own Health Summary (for the logged-in elderly user)
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        data = get_dashboard_data(user_id)
        user = data.get("user", {})

        # Header
        st.markdown(f"""
        <div class="welcome-card" style="padding:1.25rem 1.5rem">
            <h1 style="font-size:1.4rem">👤 {user.get('full_name') or user.get('username','User')}</h1>
            <p>Age: {user.get('age','—')} · Last active: {str(user.get('last_login','—'))[:16]}</p>
        </div>""", unsafe_allow_html=True)

        # ── KPI Row ───────────────────────────────────────────────────────────
        k1, k2, k3, k4 = st.columns(4)
        med_stats  = data["medicine_stats"]
        rem_stats  = data["reminder_stats"]
        mood_stats = data["mood_stats"]
        em_stats   = data["emergency_stats"]

        with k1:
            c = "#00B894" if med_stats["adherence_pct"] >= 80 else "#FDCB6E" if med_stats["adherence_pct"] >= 50 else "#E17055"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:{c}">
                <div class="metric-value" style="color:{c}">{med_stats['adherence_pct']}%</div>
                <div class="metric-label">💊 Med Adherence (7d)</div>
            </div>""", unsafe_allow_html=True)
        with k2:
            c2 = "#00B894" if rem_stats["completion_pct"] >= 80 else "#FDCB6E"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:{c2}">
                <div class="metric-value" style="color:{c2}">{rem_stats['completion_pct']}%</div>
                <div class="metric-label">✅ Task Completion (7d)</div>
            </div>""", unsafe_allow_html=True)
        with k3:
            mood_emoji = config.MOODS.get(mood_stats.get("dominant","neutral"),{}).get("emoji","😐")
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:#FF6584">
                <div class="metric-value">{mood_emoji} {mood_stats.get('avg_score',0)}/10</div>
                <div class="metric-label">🎭 Avg Mood Score (30d)</div>
            </div>""", unsafe_allow_html=True)
        with k4:
            em_c = "#E17055" if em_stats["total"] > 2 else "#FDCB6E" if em_stats["total"] > 0 else "#00B894"
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:{em_c}">
                <div class="metric-value" style="color:{em_c}">{em_stats['total']}</div>
                <div class="metric-label">🚨 Emergency Incidents</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Mood trend chart ──────────────────────────────────────────────────
        mood_hist = data["mood_history"]
        if mood_hist:
            df_mood = pd.DataFrame(mood_hist)
            df_mood["date"] = pd.to_datetime(df_mood["logged_at"]).dt.date
            daily_mood = df_mood.groupby("date")["mood_score"].mean().reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_mood["date"], y=daily_mood["mood_score"],
                mode="lines+markers",
                line=dict(color="#FF6584", width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(255,101,132,0.1)",
                name="Mood Score",
            ))
            fig.add_hline(y=5, line_dash="dot", line_color="#999", annotation_text="Neutral")
            fig.update_layout(
                title="Mood Trend – Last 14 Days",
                yaxis=dict(range=[0,10], title="Score"),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=260,
                margin=dict(t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── Today's medicine status table ─────────────────────────────────────
        left, right = st.columns(2)

        with left:
            st.markdown("**💊 Today's Medicines**")
            today_meds = data["today_medicines"]
            if not today_meds:
                st.info("No medicines today.")
            else:
                for m in today_meds:
                    badge = {"taken":"badge-taken","missed":"badge-missed","pending":"badge-pending"}.get(m["status"],"badge-pending")
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                         padding:0.5rem 0.75rem;margin:3px 0;background:#f9f9ff;border-radius:8px">
                        <span>💊 {m['name']} <small style='color:#636E72'>({m['time_slot']})</small></span>
                        <span class="status-badge {badge}">{m['status'].upper()}</span>
                    </div>""", unsafe_allow_html=True)

        with right:
            st.markdown("**⏰ Today's Reminders**")
            today_rems = data["today_reminders"]
            if not today_rems:
                st.info("No reminders today.")
            else:
                for r in today_rems:
                    icon = "✅" if r["status"]=="completed" else "⏳"
                    st.markdown(f"""
                    <div style="padding:0.5rem 0.75rem;margin:3px 0;background:#f9f9ff;border-radius:8px">
                        {icon} <strong>{r['title']}</strong> <small style='color:#636E72'>@ {r['time']}</small>
                    </div>""", unsafe_allow_html=True)

        # ── Recent emergencies ────────────────────────────────────────────────
        recent_em = data["recent_emergencies"]
        if recent_em:
            st.markdown("**🚨 Recent Emergency Events**")
            for e in recent_em:
                sev_icon = {"critical":"🔴","high":"🟠","medium":"🟡"}.get(e["severity"],"⚪")
                st.markdown(f"""
                <div style="padding:0.5rem 0.75rem;margin:3px 0;background:#fff5f5;border-radius:8px;border-left:3px solid #E17055">
                    {sev_icon} <strong>{e['emergency_type'].replace('_',' ').title()}</strong>
                    <small style='color:#636E72;float:right'>{str(e['created_at'])[:16]}</small><br>
                    <small>"{e['trigger_text'][:80]}…"</small>
                </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – View a Linked Patient
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        linked = get_linked_patients(username)
        if not linked:
            st.info("You are not linked as a caregiver to any patient yet. "
                    "Ask the elderly user to add you from their 'Manage Access' tab.")
        else:
            patient_names = {f"{p['full_name'] or p['username']} (ID: {p['id']})": p["id"]
                             for p in linked}
            selected_label = st.selectbox("Select Patient", list(patient_names.keys()), key="cg_patient_select")
            patient_id = patient_names[selected_label]

            if st.button("📊 Load Dashboard", type="primary", key="load_patient_btn"):
                with st.spinner("Loading patient data…"):
                    p_data = get_dashboard_data(patient_id)
                st.session_state["caregiver_patient_data"] = p_data

            p_data = st.session_state.get("caregiver_patient_data")
            if p_data:
                p_user     = p_data.get("user", {})
                p_med      = p_data["medicine_stats"]
                p_mood     = p_data["mood_stats"]
                p_rem      = p_data["reminder_stats"]
                p_em       = p_data["emergency_stats"]

                st.markdown(f"### 👤 {p_user.get('full_name','Patient')} — Health Overview")

                kc1, kc2, kc3, kc4 = st.columns(4)
                kc1.metric("Med Adherence", f"{p_med['adherence_pct']}%")
                kc2.metric("Task Completion", f"{p_rem['completion_pct']}%")
                kc3.metric("Avg Mood", f"{p_mood.get('avg_score',0)}/10")
                kc4.metric("Emergencies", p_em["total"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Manage Access
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        caregivers = get_caregivers(user_id)
        st.markdown(f"#### 🔗 People With Access To Your Dashboard ({len(caregivers)})")

        if not caregivers:
            st.info("No caregivers linked yet. Add a family member or healthcare provider below.")
        else:
            for cg in caregivers:
                cc1, cc2 = st.columns([5,1])
                with cc1:
                    st.markdown(f"""
                    <div class="info-card" style="padding:0.65rem 1rem;margin-bottom:0.35rem">
                        👤 <strong>{cg['caregiver_username']}</strong> ·
                        <span style='color:#636E72'>Permission: {cg['permission_level'].title()}</span> ·
                        <small style='color:#999'>Added {str(cg['added_at'])[:10]}</small>
                    </div>""", unsafe_allow_html=True)
                with cc2:
                    if st.button("🗑️", key=f"rm_cg_{cg['id']}", help="Remove access"):
                        remove_caregiver(cg["id"])
                        st.rerun()

        st.markdown("---")
        st.markdown("#### ➕ Grant Access to a Caregiver")
        with st.form("add_caregiver_form", clear_on_submit=True):
            cg_username = st.text_input("Their CareCompanion Username *",
                                        placeholder="e.g. priya_sharma")
            cg_perm     = st.selectbox("Permission Level", ["view", "full"])
            if st.form_submit_button("🔗 Grant Access", type="primary", use_container_width=True):
                res = add_caregiver(user_id, cg_username, cg_perm)
                if res["success"]:
                    st.success(res["message"])
                    st.rerun()
                else:
                    st.error(res["message"])
