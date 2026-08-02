"""
pages/mood.py – Mood Tracker
AI-powered mood detection, daily logging, weekly/monthly Plotly charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from services.mood_service import (
    analyze_mood, log_mood, get_mood_history,
    get_mood_statistics, get_today_mood,
)
from authentication.auth import get_current_user_id
import config


def render():
    user_id = get_current_user_id()

    st.markdown('<div class="page-title">🎭 Mood Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Track your emotions and understand your wellbeing</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Log Mood", "📊 Weekly View", "📅 Monthly Trends"])

    # ── Tab 1: Log today's mood ───────────────────────────────────────────────
    with tab1:
        today_log = get_today_mood(user_id)
        if today_log:
            mood_meta = config.MOODS.get(today_log["mood"], {})
            st.markdown(f"""
            <div class="info-card" style="border-left:4px solid {mood_meta.get('color','#6C63FF')}">
                <h4>Today's Mood: {mood_meta.get('emoji','😐')} {today_log['mood'].title()}</h4>
                <p style="color:#636E72">Score: {today_log['mood_score']}/10 · Logged at {str(today_log['logged_at'])[:16]}</p>
                {f"<p>{today_log['suggestions']}</p>" if today_log.get('suggestions') else ""}
            </div>""", unsafe_allow_html=True)

        st.markdown("#### 🤔 How are you feeling right now?")

        # Quick mood picker
        st.markdown("**Choose your mood:**")
        mood_cols = st.columns(5)
        mood_list = list(config.MOODS.items())
        for i, (mood, meta) in enumerate(mood_list):
            with mood_cols[i % 5]:
                label = f"{meta['emoji']} {mood.title()}"
                if st.button(label, key=f"mood_pick_{mood}", use_container_width=True):
                    st.session_state["selected_mood"] = mood

        selected = st.session_state.get("selected_mood")
        if selected:
            meta = config.MOODS.get(selected, {})
            st.markdown(f"""
            <div class="mood-chip" style="margin:0.5rem 0">
                {meta.get('emoji','')} Feeling <strong>{selected.title()}</strong>
            </div>""", unsafe_allow_html=True)

        st.markdown("#### ✍️ Tell me more (optional)")
        mood_text = st.text_area(
            "Describe how you're feeling, what happened today, or anything on your mind…",
            height=110, key="mood_text_input", label_visibility="collapsed",
            placeholder="I woke up feeling a bit tired today, but the morning tea helped…"
        )
        mood_notes = st.text_input("Any specific notes?", placeholder="E.g. 'Visited the doctor'", key="mood_notes_input")

        col_ai, col_log = st.columns(2)

        with col_ai:
            if st.button("🤖 Analyse Mood with AI", type="secondary", use_container_width=True, key="analyse_mood_btn"):
                if mood_text.strip():
                    with st.spinner("Analysing your mood…"):
                        result = analyze_mood(mood_text)
                    st.session_state["mood_analysis"] = result
                    st.session_state["selected_mood"] = result["mood"]
                else:
                    st.warning("Please write something first so I can analyse your mood.")

        analysis = st.session_state.get("mood_analysis")
        if analysis:
            meta = config.MOODS.get(analysis["mood"], {})
            st.markdown(f"""
            <div class="info-card">
                <h4>AI Analysis: {meta.get('emoji','😐')} {analysis['mood'].title()} (Score: {analysis['mood_score']}/10)</h4>
                <p><strong>Possible triggers:</strong> {analysis.get('triggers','—')}</p>
                <p><strong>Suggestions:</strong> {analysis.get('suggestions','—')}</p>
            </div>""", unsafe_allow_html=True)

        with col_log:
            if st.button("💾 Save Mood Log", type="primary", use_container_width=True, key="save_mood_btn"):
                mood_to_log = selected or (analysis["mood"] if analysis else None)
                if not mood_to_log:
                    st.warning("Please select or analyse a mood first.")
                else:
                    score = config.MOODS.get(mood_to_log, {}).get("score", 5)
                    if analysis:
                        score = analysis["mood_score"]
                    log_mood(
                        user_id, mood_to_log, score,
                        notes=mood_notes or mood_text[:200],
                        triggers=analysis.get("triggers","") if analysis else "",
                        suggestions=analysis.get("suggestions","") if analysis else "",
                    )
                    st.session_state.pop("mood_analysis", None)
                    st.session_state.pop("selected_mood", None)
                    st.success(f"✅ Mood logged: {mood_to_log.title()}!")
                    st.rerun()

    # ── Tab 2: Weekly View ────────────────────────────────────────────────────
    with tab2:
        history_7 = get_mood_history(user_id, days=7)
        if not history_7:
            st.info("📭 No mood logs for the past week. Start logging your mood daily!")
        else:
            df = pd.DataFrame(history_7)
            df["date"]  = pd.to_datetime(df["logged_at"]).dt.date
            df["day"]   = pd.to_datetime(df["logged_at"]).dt.strftime("%a %d")
            daily_avg   = df.groupby("day")["mood_score"].mean().reset_index()
            daily_avg.columns = ["Day", "Average Score"]

            # Bar chart
            fig = px.bar(
                daily_avg, x="Day", y="Average Score",
                color="Average Score",
                color_continuous_scale=["#E17055","#FDCB6E","#55EFC4"],
                range_color=[1, 10],
                title="📊 Mood Score – Last 7 Days",
                text_auto=".1f",
            )
            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito", size=13),
                yaxis=dict(range=[0,10], title="Mood Score (1–10)"),
                coloraxis_showscale=False,
                height=320,
                margin=dict(t=50, b=30),
            )
            fig.update_traces(marker_line_width=0, textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # Mood counts
            mood_counts = df["mood"].value_counts().reset_index()
            mood_counts.columns = ["Mood", "Count"]
            colors = [config.MOODS.get(m, {}).get("color", "#6C63FF") for m in mood_counts["Mood"]]
            fig2 = px.pie(
                mood_counts, values="Count", names="Mood",
                title="Mood Distribution", hole=0.45,
                color_discrete_sequence=colors,
            )
            fig2.update_layout(font=dict(family="Nunito"), height=300, margin=dict(t=50))
            st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Monthly Trends ─────────────────────────────────────────────────
    with tab3:
        stats = get_mood_statistics(user_id, days=30)
        history_30 = get_mood_history(user_id, days=30)

        # KPI row
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Average Score", f"{stats['avg_score']}/10")
        with k2:
            dominant = stats.get("dominant", "—")
            meta     = config.MOODS.get(dominant, {})
            st.metric("Most Frequent Mood", f"{meta.get('emoji','')} {dominant.title()}")
        with k3:
            trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(stats.get("trend",""), "—")
            st.metric("30-Day Trend", f"{trend_icon} {stats.get('trend','—').title()}")

        if history_30:
            df30 = pd.DataFrame(history_30)
            df30["Date"] = pd.to_datetime(df30["logged_at"]).dt.date

            daily30 = df30.groupby("Date")["mood_score"].mean().reset_index()
            daily30.columns = ["Date", "Score"]

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=daily30["Date"], y=daily30["Score"],
                mode="lines+markers",
                line=dict(color="#6C63FF", width=2.5, shape="spline"),
                marker=dict(size=6, color="#6C63FF"),
                fill="tozeroy", fillcolor="rgba(108,99,255,0.08)",
                name="Mood Score",
            ))
            fig3.add_hline(y=5, line_dash="dot", line_color="#999",
                           annotation_text="Neutral (5)")
            fig3.update_layout(
                title="📈 30-Day Mood Trend",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Nunito", size=13),
                yaxis=dict(range=[0,10], title="Mood Score"),
                xaxis_title="Date",
                height=320, margin=dict(t=50, b=30),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No mood logs yet for the past 30 days.")
