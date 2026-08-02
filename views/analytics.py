"""
pages/analytics.py – Health Analytics Dashboard
Comprehensive Plotly charts: mood, medicine adherence, reminders, emergencies.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta, date

from services.mood_service       import get_mood_history, get_mood_statistics
from services.medicine_service   import get_medicine_logs, get_adherence_stats, get_medicines
from services.reminder_service   import get_completion_stats
from services.emergency_service  import get_emergency_logs, get_emergency_stats
from services.chat_service       import get_conversation_history, get_conversation_count
from authentication.auth         import get_current_user_id
import config


def render():
    user_id = get_current_user_id()

    st.markdown('<div class="page-title">📊 Health Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Your personal health insights at a glance</div>',
                unsafe_allow_html=True)

    # ── Period selector ───────────────────────────────────────────────────────
    period = st.selectbox("📅 Period", [7, 14, 30, 90],
                          format_func=lambda x: f"Last {x} days",
                          index=1, key="analytics_period")

    st.markdown("---")

    # ══════════════════════════════════════════════════════════════════════════
    # OVERVIEW KPIs
    # ══════════════════════════════════════════════════════════════════════════
    med_stats  = get_adherence_stats(user_id, days=period)
    mood_stats = get_mood_statistics(user_id, days=period)
    rem_stats  = get_completion_stats(user_id, days=period)
    em_stats   = get_emergency_stats(user_id)
    conv_count = get_conversation_count(user_id)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        c = "#00B894" if med_stats["adherence_pct"]>=80 else "#FDCB6E" if med_stats["adherence_pct"]>=50 else "#E17055"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{c}">
            <div class="metric-value" style="color:{c}">{med_stats['adherence_pct']}%</div>
            <div class="metric-label">💊 Med Adherence</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#FF6584">
            <div class="metric-value">{mood_stats.get('avg_score',0)}/10</div>
            <div class="metric-label">🎭 Avg Mood Score</div></div>""", unsafe_allow_html=True)
    with k3:
        c2 = "#00B894" if rem_stats["completion_pct"]>=80 else "#FDCB6E"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{c2}">
            <div class="metric-value" style="color:{c2}">{rem_stats['completion_pct']}%</div>
            <div class="metric-label">✅ Task Completion</div></div>""", unsafe_allow_html=True)
    with k4:
        ec = "#E17055" if em_stats["total"]>2 else "#FDCB6E" if em_stats["total"]>0 else "#00B894"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{ec}">
            <div class="metric-value" style="color:{ec}">{em_stats['total']}</div>
            <div class="metric-label">🚨 Emergencies</div></div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#43C6AC">
            <div class="metric-value">{conv_count}</div>
            <div class="metric-label">💬 Total Chats</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # ROW 1 – Mood + Medicine side-by-side
    # ══════════════════════════════════════════════════════════════════════════
    col1, col2 = st.columns(2)

    # Mood trend
    with col1:
        mood_hist = get_mood_history(user_id, days=period)
        if mood_hist:
            df = pd.DataFrame(mood_hist)
            df["date"] = pd.to_datetime(df["logged_at"]).dt.date
            daily = df.groupby("date")["mood_score"].mean().reset_index()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily["date"], y=daily["mood_score"],
                mode="lines+markers",
                line=dict(color="#FF6584", width=2.5, shape="spline"),
                marker=dict(size=6),
                fill="tozeroy", fillcolor="rgba(255,101,132,0.08)",
                name="Mood",
            ))
            fig.add_hline(y=5, line_dash="dot", line_color="#999",
                          annotation_text="Neutral")
            fig.update_layout(
                title="🎭 Mood Score Over Time",
                yaxis=dict(range=[0,10], title="Score"),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=280,
                margin=dict(t=45,b=25),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No mood data for this period.")

    # Medicine adherence
    with col2:
        med_logs = get_medicine_logs(user_id, days=period)
        if med_logs:
            df = pd.DataFrame(med_logs)
            df["date"] = pd.to_datetime(df["scheduled_time"]).dt.date
            taken = df[df["status"]=="taken"].groupby("date").size().reset_index(name="taken")
            total = df.groupby("date").size().reset_index(name="total")
            m = pd.merge(total, taken, on="date", how="left").fillna(0)
            m["pct"] = (m["taken"]/m["total"]*100).round(1)

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=m["date"], y=m["pct"],
                marker=dict(
                    color=m["pct"],
                    colorscale=[[0,"#E17055"],[0.5,"#FDCB6E"],[1,"#00B894"]],
                    cmin=0, cmax=100,
                ),
                name="Adherence %",
                text=m["pct"].apply(lambda x: f"{x:.0f}%"),
                textposition="outside",
            ))
            fig2.add_hline(y=80, line_dash="dot", line_color="#00B894",
                           annotation_text="Target 80%")
            fig2.update_layout(
                title="💊 Medicine Adherence %",
                yaxis=dict(range=[0,115], title="%", ticksuffix="%"),
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=280,
                margin=dict(t=45,b=25),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No medicine log data for this period.")

    # ══════════════════════════════════════════════════════════════════════════
    # ROW 2 – Mood distribution + Reminder completion
    # ══════════════════════════════════════════════════════════════════════════
    col3, col4 = st.columns(2)

    with col3:
        mood_counts = mood_stats.get("mood_counts", {})
        if mood_counts:
            labels = list(mood_counts.keys())
            values = list(mood_counts.values())
            colors = [config.MOODS.get(m,{}).get("color","#6C63FF") for m in labels]
            fig3 = go.Figure(data=[go.Pie(
                labels=[f"{config.MOODS.get(l,{}).get('emoji','')} {l.title()}" for l in labels],
                values=values, hole=0.45,
                marker=dict(colors=colors),
                textinfo="label+percent",
            )])
            fig3.update_layout(
                title="🎭 Mood Distribution",
                font=dict(family="Nunito"), height=300,
                margin=dict(t=45, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No mood distribution data.")

    with col4:
        # Reminder completion stacked bar (dummy if no data)
        rem_logs_raw = []
        try:
            from database.connection import fetch_all
            from utils.helpers import days_ago
            rem_logs_raw = fetch_all(
                "SELECT DATE(scheduled_time) as d, status FROM reminder_logs WHERE user_id=? AND scheduled_time>=?",
                (user_id, days_ago(period))
            )
        except Exception:
            pass

        if rem_logs_raw:
            df_r = pd.DataFrame(rem_logs_raw)
            pivot = df_r.groupby(["d","status"]).size().unstack(fill_value=0).reset_index()
            fig4 = go.Figure()
            if "completed" in pivot.columns:
                fig4.add_trace(go.Bar(x=pivot["d"], y=pivot["completed"],
                                      name="Completed", marker_color="#00B894"))
            if "missed" in pivot.columns:
                fig4.add_trace(go.Bar(x=pivot["d"], y=pivot["missed"],
                                      name="Missed", marker_color="#E17055"))
            fig4.update_layout(
                barmode="stack", title="✅ Daily Reminder Completion",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=300,
                margin=dict(t=45,b=25),
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No reminder log data for this period.")

    # ══════════════════════════════════════════════════════════════════════════
    # ROW 3 – Emergency timeline + Per-medicine breakdown
    # ══════════════════════════════════════════════════════════════════════════
    em_logs = get_emergency_logs(user_id, limit=50)
    if em_logs:
        st.markdown("---")
        df_em = pd.DataFrame(em_logs)
        df_em["date"] = pd.to_datetime(df_em["created_at"]).dt.date
        by_type = df_em.groupby("emergency_type").size().reset_index(name="count")

        ec1, ec2 = st.columns(2)
        with ec1:
            fig5 = px.bar(
                by_type, x="emergency_type", y="count",
                color="count",
                color_continuous_scale=["#FDCB6E","#E17055"],
                title="🚨 Emergency Events by Type",
                text="count",
            )
            fig5.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=260,
                margin=dict(t=45,b=25), coloraxis_showscale=False,
                xaxis_title="Type", yaxis_title="Count",
            )
            fig5.update_traces(textposition="outside")
            st.plotly_chart(fig5, use_container_width=True)

        with ec2:
            daily_em = df_em.groupby("date").size().reset_index(name="count")
            fig6 = go.Figure()
            fig6.add_trace(go.Scatter(
                x=daily_em["date"], y=daily_em["count"],
                mode="markers+lines", marker=dict(color="#E17055", size=8),
                line=dict(color="#E17055", width=1.5),
                name="Incidents",
            ))
            fig6.update_layout(
                title="📅 Emergency Timeline",
                yaxis_title="Count", xaxis_title="Date",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito"), height=260,
                margin=dict(t=45,b=25),
            )
            st.plotly_chart(fig6, use_container_width=True)

    # ── Per-medicine breakdown table ──────────────────────────────────────────
    medicines = get_medicines(user_id)
    if medicines and med_logs:
        st.markdown("---")
        st.markdown("#### 💊 Per-Medicine Adherence Summary")
        df_ml = pd.DataFrame(med_logs)
        if "medicine_name" in df_ml.columns:
            breakdown = df_ml.groupby(["medicine_name","status"]).size().unstack(fill_value=0).reset_index()
            for col in ["taken","missed","pending","skipped"]:
                if col not in breakdown.columns:
                    breakdown[col] = 0
            breakdown["total"]   = breakdown[["taken","missed","pending"]].sum(axis=1)
            breakdown["adh_pct"] = (breakdown["taken"]/breakdown["total"]*100).round(1).fillna(0)
            display = breakdown.rename(columns={"medicine_name":"Medicine",
                                                 "adh_pct":"Adherence %"})
            st.dataframe(display[["Medicine","taken","missed","pending","Adherence %"]],
                         use_container_width=True)
