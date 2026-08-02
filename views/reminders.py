"""
pages/reminders.py – Daily Routine Reminders
Add, manage and complete reminders. Calendar-style today view.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime

from services.reminder_service import (
    add_reminder, get_reminders, get_reminder, update_reminder,
    delete_reminder, toggle_reminder, complete_reminder,
    get_today_reminders, get_completion_stats,
)
from authentication.auth import get_current_user_id
import config

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def render():
    user_id = get_current_user_id()

    st.markdown('<div class="page-title">⏰ Daily Reminders</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Stay on schedule, build healthy habits</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📅 Today", "📋 All Reminders", "➕ New Reminder"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 – Today's reminders
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        today_rems = get_today_reminders(user_id)
        weekday    = datetime.now().strftime("%A")
        now_time   = datetime.now().strftime("%H:%M")

        st.markdown(f"#### 📆 {datetime.now().strftime('%A, %d %B %Y')}")

        if not today_rems:
            st.info(f"No reminders set for {weekday}. Add one below!")
        else:
            done  = sum(1 for r in today_rems if r["status"] == "completed")
            total = len(today_rems)
            pct   = round(done / total * 100) if total else 0

            st.markdown(f"""
            <div style="margin-bottom:1rem">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <strong>Today's Completion</strong>
                    <strong style="color:{'#00B894' if pct>=80 else '#FDCB6E' if pct>=50 else '#636E72'}">{pct}% ({done}/{total})</strong>
                </div>
                <div class="cc-progress-bg">
                    <div class="cc-progress-fill" style="width:{pct}%;background:{'linear-gradient(90deg,#00B894,#43C6AC)' if pct>=80 else 'linear-gradient(90deg,#FDCB6E,#F39C12)'}"></div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Group by time
            time_groups: dict[str, list] = {}
            for rem in today_rems:
                t = rem["time"]
                time_groups.setdefault(t, []).append(rem)

            for t, rems in sorted(time_groups.items()):
                is_past = t <= now_time
                time_color = "#636E72" if is_past else "#6C63FF"
                st.markdown(f"<div style='color:{time_color};font-weight:700;margin:0.75rem 0 0.25rem'>🕐 {t}</div>",
                            unsafe_allow_html=True)

                for rem in rems:
                    is_done = rem["status"] == "completed"
                    ic      = "✅" if is_done else ("⏰" if not is_past else "⚠️")
                    type_icons = {
                        "Wake Up":"☀️","Breakfast":"🥣","Exercise":"🏋️","Walk":"🚶",
                        "Yoga":"🧘","Lunch":"🍽️","Doctor Visit":"🏥","Family Call":"📞",
                        "Dinner":"🍲","Medication":"💊","Sleep":"😴","General":"📌",
                    }
                    type_icon = type_icons.get(rem["reminder_type"], "📌")

                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"""
                        <div class="info-card" style="padding:0.65rem 1rem;margin-bottom:0.35rem;
                             {'opacity:0.65;' if is_done else ''}border-left:4px solid {'#00B894' if is_done else '#6C63FF'}">
                            <strong>{ic} {type_icon} {rem['title']}</strong>
                            {f"<br><small style='color:#636E72'>{rem['description']}</small>" if rem.get('description') else ''}
                        </div>""", unsafe_allow_html=True)
                    with col_btn:
                        if not is_done:
                            if st.button("✓ Done", key=f"comp_{rem['id']}_{t}", use_container_width=True):
                                complete_reminder(user_id, rem["id"], rem["scheduled_time"])
                                st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 – All Reminders
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        reminders = get_reminders(user_id, active_only=False)
        if not reminders:
            st.info("No reminders yet. Create your first one!")
        else:
            stats = get_completion_stats(user_id, days=7)
            k1, k2, k3 = st.columns(3)
            k1.metric("7-Day Completion", f"{stats['completion_pct']}%")
            k2.metric("✅ Completed",      stats["completed"])
            k3.metric("❌ Missed",         stats["missed"])

            st.markdown("---")

            for rem in reminders:
                active    = bool(rem.get("is_active", 1))
                days_str  = ", ".join(d.title() for d in (rem.get("days") or []))
                status_dot = "🟢" if active else "⚫"

                with st.expander(f"{status_dot} {rem['title']} @ {rem['time']}", expanded=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"""
                        **Type:** {rem['reminder_type']}
                        **Time:** {rem['time']}
                        **Days:** {days_str or 'None set'}
                        """)
                    with c2:
                        st.markdown(f"""
                        **Description:** {rem.get('description','—') or '—'}
                        **Status:** {'Active' if active else 'Disabled'}
                        """)

                    bc1, bc2, bc3, bc4 = st.columns(4)
                    with bc1:
                        lbl = "⏸ Disable" if active else "▶ Enable"
                        if st.button(lbl, key=f"tog_{rem['id']}", use_container_width=True):
                            toggle_reminder(rem["id"], not active)
                            st.rerun()
                    with bc2:
                        if st.button("✏️ Edit", key=f"edit_rem_{rem['id']}", use_container_width=True):
                            st.session_state["edit_reminder_id"] = rem["id"]
                    with bc3:
                        if st.button("🗑️ Delete", key=f"del_rem_{rem['id']}", use_container_width=True):
                            delete_reminder(rem["id"])
                            st.rerun()

                    # Inline edit form
                    if st.session_state.get("edit_reminder_id") == rem["id"]:
                        st.markdown("---")
                        with st.form(key=f"edit_rem_form_{rem['id']}"):
                            ef_title = st.text_input("Title", value=rem["title"])
                            ef_desc  = st.text_area("Description", value=rem.get("description",""), height=70)
                            ef_type  = st.selectbox("Type", config.REMINDER_TYPES,
                                                    index=config.REMINDER_TYPES.index(rem["reminder_type"])
                                                    if rem["reminder_type"] in config.REMINDER_TYPES else 0)
                            ef_time  = st.text_input("Time (HH:MM)", value=rem["time"])
                            ef_days  = st.multiselect("Days", DAYS_OF_WEEK,
                                                      default=[d.title() for d in (rem.get("days") or [])])
                            if st.form_submit_button("💾 Update", use_container_width=True):
                                res = update_reminder(rem["id"], ef_title, ef_desc, ef_type,
                                                      ef_time, [d.lower() for d in ef_days])
                                if res["success"]:
                                    st.success(res["message"])
                                    st.session_state.pop("edit_reminder_id", None)
                                    st.rerun()
                                else:
                                    st.error(res["message"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 – New Reminder
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### ➕ Create a New Reminder")

        # Preset quick-add buttons
        st.markdown("**Quick Presets:**")
        presets = [
            ("☀️ Wake Up",    "Wake Up",      "07:00", ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]),
            ("🥣 Breakfast",  "Breakfast",    "08:00", ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]),
            ("🚶 Morning Walk","Walk",          "09:00", ["monday","wednesday","friday"]),
            ("🧘 Yoga",        "Yoga",          "07:30", ["monday","wednesday","friday"]),
            ("🍽️ Lunch",       "Lunch",        "13:00", ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]),
            ("😴 Bedtime",     "Sleep",        "22:00", ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]),
        ]
        pre_cols = st.columns(3)
        for i, (icon_label, rtype, t, days) in enumerate(presets):
            with pre_cols[i % 3]:
                if st.button(icon_label, key=f"preset_{i}", use_container_width=True):
                    res = add_reminder(user_id, icon_label.split(" ",1)[1], "", rtype, t, days)
                    if res["success"]:
                        st.success(f"✅ {icon_label} reminder added!")
                        st.rerun()

        st.markdown("---")
        st.markdown("**Custom Reminder:**")
        with st.form("add_reminder_form", clear_on_submit=True):
            f_title = st.text_input("Title *", placeholder="e.g. Evening Walk")
            f_desc  = st.text_area("Description (optional)", height=70,
                                   placeholder="e.g. Walk for 20 minutes in the park")
            fc1, fc2 = st.columns(2)
            f_type   = fc1.selectbox("Category", config.REMINDER_TYPES)
            f_time   = fc2.text_input("Time (HH:MM) *", placeholder="09:00")
            f_days   = st.multiselect("Repeat on days *", DAYS_OF_WEEK, default=["Monday","Wednesday","Friday"])

            if st.form_submit_button("➕ Add Reminder", type="primary", use_container_width=True):
                res = add_reminder(user_id, f_title, f_desc, f_type, f_time,
                                   [d.lower() for d in f_days])
                if res["success"]:
                    st.success(res["message"])
                    st.balloons()
                else:
                    st.error(res["message"])
