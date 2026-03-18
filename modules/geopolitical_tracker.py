"""MODULE 2 -- GEOPOLITICAL IMPACT TRACKER"""
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
    st.markdown(
        '<div class="dashboard-header">'
        '<div class="header-left">'
        '<span style="color:#F0F0F5;font-weight:700;font-size:1.4rem;">'
        'Geopolitical Tracker</span>'
        '</div>'
        '<div class="header-right">'
        '<span style="color:#6B6B80;font-size:0.8rem;">Sources: Google News RSS, GDELT</span>'
        '</div></div>',
        unsafe_allow_html=True
    )

    news = fetch_conflict_news()
    intensity = _compute_conflict_intensity(news)
    signal = _war_signal(intensity)

    # --- Stat cards ---
    col1, col2, col3 = st.columns(3)
    with col1:
        bar_color = "#3DD598" if intensity < 4 else ("#FFC542" if intensity < 7 else "#FC5A5A")
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="label">Conflict Intensity</div>'
            f'<div class="value">{intensity}/10</div>'
            f'<div style="background:#1E1E2D;border-radius:4px;height:6px;margin-top:4px;">'
            f'<div style="background:{bar_color};width:{intensity*10}%;height:100%;'
            f'border-radius:4px;transition:width 0.5s;"></div></div>'
            f'</div>', unsafe_allow_html=True
        )
    with col2:
        signal_colors = {"GREEN": "#3DD598", "AMBER": "#FFC542", "RED": "#FC5A5A"}
        signal_icons = {"GREEN": "\U0001f7e2", "AMBER": "\U0001f7e1", "RED": "\U0001f534"}
        sc = signal_colors[signal]
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="label">War-Economy Signal</div>'
            f'<div class="value">{signal_icons[signal]} {signal}</div>'
            f'<span class="trend {"up" if signal == "GREEN" else "down"}">'
            f'{"Accumulate" if signal == "GREEN" else ("Hold" if signal == "AMBER" else "Reduce Risk")}'
            f'</span></div>', unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="label">Active Conflict Events</div>'
            f'<div class="value">{len(news)}</div>'
            f'<span style="color:#6B6B80;font-size:0.72rem;">From 5 keyword streams</span>'
            f'</div>', unsafe_allow_html=True
        )

    # --- Signal action box ---
    signal_map = {"GREEN": "success", "AMBER": "warning", "RED": "error"}
    action_map = {
        "GREEN": "ACCUMULATE \u2014 Conflict at baseline. Continue SIP into Defence + Gold.",
        "AMBER": "HOLD \u2014 Elevated tension. Maintain positions, avoid new risk.",
        "RED": "REDUCE RISK \u2014 Active escalation. Increase Gold, reduce tech exposure."
    }
    getattr(st, signal_map[signal])(f"**Signal: {signal}** \u2014 {action_map[signal]}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- News feed with severity accent ---
    st.markdown(
        '<div class="section-header"><h3>Live Conflict News Feed</h3></div>',
        unsafe_allow_html=True
    )

    high_kw = ["strike", "attack", "bomb", "invasion", "nuclear", "missile", "escalat"]
    med_kw = ["tension", "military", "deploy", "sanction", "threat"]

    if news:
        for article in news[:10]:
            title_lower = article["title"].lower()
            severity = "high" if any(k in title_lower for k in high_kw) else \
                       ("medium" if any(k in title_lower for k in med_kw) else "low")
            st.markdown(
                f'<div class="news-item-accent {severity}">'
                f'<div style="color:#E0E0E8;font-weight:600;font-size:0.88rem;">'
                f'{article["title"]}</div>'
                f'<div style="color:#6B6B80;font-size:0.75rem;margin-top:4px;">'
                f'{article["source"]} | {article["published"][:25]} | '
                f'Tag: {article["keyword"]}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("No conflict news available at this time.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Scenario table ---
    st.markdown(
        '<div class="section-header"><h3>Geopolitical Scenario Impact Map</h3></div>',
        unsafe_allow_html=True
    )
    scenario_df = pd.DataFrame(SCENARIOS)
    scenario_df.columns = ["Conflict Scenario", "Winner Category", "Loser Category",
                           "Probability", "Timeline", "Investor Action"]
    st.dataframe(scenario_df, use_container_width=True, hide_index=True)
