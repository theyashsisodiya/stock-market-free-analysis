"""MODULE 2 — GEOPOLITICAL IMPACT TRACKER"""
import streamlit as st
import pandas as pd
from data.fetchers import fetch_conflict_news
from config import SCENARIOS


def _compute_conflict_intensity(news: list) -> int:
    """Derive a 0-10 intensity score from news volume and keywords."""
    if not news:
        return 2
    high_keywords = ["strike", "attack", "bomb", "invasion", "nuclear", "missile", "escalat"]
    med_keywords = ["tension", "military", "deploy", "sanction", "threat", "drill"]
    score = min(len(news) // 2, 5)
    for article in news:
        title = article.get("title", "").lower()
        if any(k in title for k in high_keywords):
            score += 1
        elif any(k in title for k in med_keywords):
            score += 0.5
    return min(int(score), 10)


def _war_signal(intensity: int) -> str:
    if intensity >= 7:
        return "RED"
    elif intensity >= 4:
        return "AMBER"
    return "GREEN"


def render():
    st.header("Module 2 — Geopolitical Impact Tracker")
    st.caption("Sources: Google News RSS, GDELT Project")

    news = fetch_conflict_news()
    intensity = _compute_conflict_intensity(news)
    signal = _war_signal(intensity)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Conflict Intensity", f"{intensity}/10")
    with col2:
        signal_colors = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
        st.metric("War-Economy Signal", f"{signal_colors.get(signal, '')} {signal}")
    with col3:
        st.metric("Active Conflict Events", len(news))

    signal_map = {"GREEN": "success", "AMBER": "warning", "RED": "error"}
    action_map = {
        "GREEN": "ACCUMULATE — Conflict at baseline. Continue SIP into Defence + Gold.",
        "AMBER": "HOLD — Elevated tension. Maintain positions, avoid new risk.",
        "RED": "REDUCE RISK — Active escalation. Increase Gold, reduce tech exposure."
    }
    getattr(st, signal_map[signal])(f"**Signal: {signal}** — {action_map[signal]}")

    st.subheader("Live Conflict News Feed")
    if news:
        for article in news[:10]:
            st.markdown(
                f'<div class="news-item">'
                f'<strong>{article["title"]}</strong><br>'
                f'<small>{article["source"]} | {article["published"][:25]} | '
                f'Tag: {article["keyword"]}</small></div>',
                unsafe_allow_html=True
            )
    else:
        st.info("No conflict news available at this time.")

    st.subheader("Geopolitical Scenario Impact Map")
    scenario_df = pd.DataFrame(SCENARIOS)
    scenario_df.columns = ["Conflict Scenario", "Winner Category", "Loser Category",
                           "Probability", "Timeline", "Investor Action"]
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
