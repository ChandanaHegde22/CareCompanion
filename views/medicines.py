"""
pages/medicines.py – Medicine Management
Full CRUD for medicines, today's schedule, adherence tracking & Plotly charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, time

from services.medicine_service import (
    add_medicine, get_medicines, get_medicine, update_medicine,
    delete_medicine, log_medicine_taken, get_today_medicines,
    get_medicine_logs, get_adherence_stats,
)
from authentication.auth import get_current_user_id
import config

FREQUENCIES   = ["Once daily", "Twice daily", "Three times daily", "Four times daily",
                 "Every 6 hours", "Every 8 hours", "Weekly", "As needed"]
MEAL_TIMINGS  = ["Before food", "After food", "With food", "Anytime"]


def render():
    user_id = get_current_user_id()

    st.markdown('<div class="page-title">💊 Medicine Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Track medications, never miss a dose</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Today", "💊 My Medicines", "➕ Add Medicine", "📊 Adherence"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Today's Schedule
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        today_meds = get_today_medicines(user_id)
        if not today_meds:
            st.info("🎉 No medicines scheduled for today. Add some using the 'Add Medicine' tab.")
        else:
            stats = get_adherence_stats(user_id, days=1)
            pct   = stats["adherence_pct"]

            # Progress bar
            st.markdown(f"""
            <div style="margin-bottom:1rem">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <strong>Today's Progress</strong>
                    <strong style="color:{'#00B894' if pct>=80 else '#FDCB6E' if pct>=50 else '#E17055'}">{pct}%</strong>
                </div>
                <div class="cc-progress-bg">
                    <div class="cc-progress-fill" style="width:{pct}%"></div>
                </div>
                <small style="color:#636E72">{stats['taken']} taken · {stats['missed']} missed · {stats['pending']} pending</small>
            </div>""", unsafe_allow_html=True)

            for med in today_meds:
                badge_map = {"taken": "badge-taken", "missed": "badge-missed", "pending": "badge-pending"}
                badge_cls = badge_map.get(med["status"], "badge-pending")
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                    <div class="info-card" style="padding:0.75rem 1rem;margin-bottom:0.4rem">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <div>
                                <strong style="font-size:1rem">💊 {med['name']}</strong>
                                <span class="status-badge {badge_cls}" style="margin-left:0.5rem">{med['status'].upper()}</span><br>
                                <small style="color:#636E72">{med['dosage']} · {med['time_slot']} · {med['meal_timing']}</small>
                                {f"<br><small style='color:#999'>{med['notes']}</small>" if med.get('notes') else ""}
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col_btn:
                    st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
                    if med["status"] != "taken":
                        if st.button("✅ Taken", key=f"taken_{med['id']}_{med['time_slot']}",
                                     use_container_width=True, type="primary"):
                            res = log_medicine_taken(user_id, med["id"], med["scheduled_time"])
                            st.success(res["message"])
                            st.rerun()
                    else:
                        st.markdown('<span style="color:#00B894;font-weight:700">✓ Done</span>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – My Medicines List
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        medicines = get_medicines(user_id)
        if not medicines:
            st.info("No medicines added yet. Click 'Add Medicine' to get started.")
        else:
            st.markdown(f"**{len(medicines)} medicine(s) active**")
            for med in medicines:
                times_str = ", ".join(med.get("times", []))
                with st.expander(f"💊 {med['name']} – {med['dosage']}", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"""
                        **Frequency:** {med['frequency']}
                        **Times:** {times_str}
                        **Meal Timing:** {med['meal_timing']}
                        **Start Date:** {med.get('start_date','—')}
                        """)
                    with c2:
                        st.markdown(f"""
                        **End Date:** {med.get('end_date','—') or 'Ongoing'}
                        **Notes:** {med.get('notes','—') or '—'}
                        **Added:** {str(med.get('created_at',''))[:10]}
                        """)

                    ec1, ec2, ec3 = st.columns(3)
                    with ec1:
                        if st.button("✏️ Edit", key=f"edit_med_{med['id']}", use_container_width=True):
                            st.session_state["editing_medicine"] = med["id"]
                    with ec2:
                        if st.button("🗑️ Remove", key=f"del_med_{med['id']}", use_container_width=True):
                            res = delete_medicine(med["id"])
                            st.success(res["message"])
                            st.rerun()

                    # Inline edit form
                    if st.session_state.get("editing_medicine") == med["id"]:
                        st.markdown("---")
                        st.markdown("**Edit Medicine**")
                        with st.form(key=f"edit_form_{med['id']}"):
                            e_name  = st.text_input("Medicine Name", value=med["name"])
                            e_dose  = st.text_input("Dosage", value=med["dosage"])
                            e_freq  = st.selectbox("Frequency", FREQUENCIES,
                                                   index=FREQUENCIES.index(med["frequency"]) if med["frequency"] in FREQUENCIES else 0)
                            e_meal  = st.selectbox("Meal Timing", MEAL_TIMINGS,
                                                   index=MEAL_TIMINGS.index(med["meal_timing"]) if med["meal_timing"] in MEAL_TIMINGS else 3)
                            e_times = st.text_input("Times (comma-separated, HH:MM)", value=", ".join(med.get("times", [])))
                            e_end   = st.text_input("End Date (YYYY-MM-DD, optional)", value=med.get("end_date",""))
                            e_notes = st.text_area("Notes", value=med.get("notes",""))
                            if st.form_submit_button("💾 Update"):
                                times_list = [t.strip() for t in e_times.split(",") if t.strip()]
                                res = update_medicine(med["id"], e_name, e_dose, e_freq,
                                                      times_list, e_meal, e_end, e_notes)
                                if res["success"]:
                                    st.success(res["message"])
                                    st.session_state.pop("editing_medicine", None)
                                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – Add Medicine
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### Add a New Medicine")
        with st.form("add_medicine_form", clear_on_submit=True):
            a_name  = st.text_input("Medicine Name *", placeholder="e.g. Metformin 500mg")
            a_dose  = st.text_input("Dosage *", placeholder="e.g. 1 tablet / 5ml / 10mg")
            a_freq  = st.selectbox("Frequency *", FREQUENCIES)
            a_meal  = st.selectbox("When to take *", MEAL_TIMINGS)

            st.markdown("**Reminder Times** (add up to 4 times)")
            tc1, tc2, tc3, tc4 = st.columns(4)
            t1 = tc1.text_input("Time 1", placeholder="08:00", key="t1")
            t2 = tc2.text_input("Time 2", placeholder="13:00", key="t2")
            t3 = tc3.text_input("Time 3", placeholder="18:00", key="t3")
            t4 = tc4.text_input("Time 4", placeholder="21:00", key="t4")

            dc1, dc2 = st.columns(2)
            a_start = dc1.text_input("Start Date (YYYY-MM-DD)", placeholder=datetime.today().strftime("%Y-%m-%d"))
            a_end   = dc2.text_input("End Date (optional)")
            a_notes = st.text_area("Notes / Instructions", placeholder="e.g. Take with warm water", height=80)

            submitted = st.form_submit_button("➕ Add Medicine", type="primary", use_container_width=True)
            if submitted:
                times = [t for t in [t1, t2, t3, t4] if t.strip()]
                res   = add_medicine(user_id, a_name, a_dose, a_freq, times,
                                     a_meal, a_start, a_end, a_notes)
                if res["success"]:
                    st.success(res["message"])
                    st.balloons()
                else:
                    st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 – Adherence Analytics
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        period = st.selectbox("Period", [7, 14, 30], format_func=lambda x: f"Last {x} days", key="adh_period")
        stats  = get_adherence_stats(user_id, days=period)
        logs   = get_medicine_logs(user_id, days=period)

        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Adherence", f"{stats['adherence_pct']}%")
        k2.metric("✅ Taken",  stats["taken"])
        k3.metric("❌ Missed", stats["missed"])
        k4.metric("⏳ Pending", stats["pending"])

        if logs:
            df = pd.DataFrame(logs)
            df["date"] = pd.to_datetime(df["scheduled_time"]).dt.date

            # Daily adherence line chart
            daily = df[df["status"]=="taken"].groupby("date").size().reset_index(name="taken")
            total = df.groupby("date").size().reset_index(name="total")
            merged = pd.merge(total, daily, on="date", how="left").fillna(0)
            merged["pct"] = (merged["taken"] / merged["total"] * 100).round(1)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=merged["date"], y=merged["pct"],
                mode="lines+markers",
                line=dict(color="#6C63FF", width=2.5, shape="spline"),
                fill="tozeroy", fillcolor="rgba(108,99,255,0.1)",
                name="Adherence %",
            ))
            fig.add_hline(y=80, line_dash="dot", line_color="#00B894",
                          annotation_text="Target 80%")
            fig.update_layout(
                title=f"📊 Medicine Adherence – Last {period} Days",
                yaxis=dict(range=[0, 105], title="Adherence %", ticksuffix="%"),
                xaxis_title="Date",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito", size=13),
                height=320, margin=dict(t=50, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Per-medicine breakdown
            if "medicine_name" in df.columns:
                by_med = df.groupby(["medicine_name","status"]).size().unstack(fill_value=0).reset_index()
                st.dataframe(by_med.rename(columns={"medicine_name":"Medicine"}), use_container_width=True)
        else:
            st.info("No medicine logs yet for this period.")
