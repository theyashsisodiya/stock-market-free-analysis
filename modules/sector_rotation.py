"""MODULE 4 -- SECTOR ROTATION HEATMAP"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import SECTORS
from data.fetchers import fetch_sector_momentum


def render():
    st.markdown(
        '<div class="dashboard-header">'
        '<div class="header-left">'
        '<span style="color:#F0F0F5;font-weight:700;font-size:1.4rem;">'
        'Sector Rotation Heatmap</span>'
        '</div></div>',
        unsafe_allow_html=True
    )
    st.caption("NSE Sectoral Indices | War-economy tilt analysis")

    rows = []
    for sector_name, meta in SECTORS.items():
        momentum = fetch_sector_momentum(meta["ticker"])
        rows.append({
            "Sector": sector_name,
            "5D Momentum %": momentum["momentum_5d"],
            "30D Momentum %": momentum["momentum_30d"],
            "War Tilt": meta["war_tilt"].upper(),
        })

    df = pd.DataFrame(rows)

    if df["5D Momentum %"].abs().sum() == 0 and df["30D Momentum %"].abs().sum() == 0:
        st.warning("Sector data unavailable \u2014 market may be closed or tickers not responding.")
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    # --- Heatmap ---
    fig = go.Figure(data=go.Heatmap(
        z=[df["5D Momentum %"].tolist(), df["30D Momentum %"].tolist()],
        x=df["Sector"].tolist(),
        y=["5-Day", "30-Day"],
        zmid=0,
        colorscale=[
            [0, "#FC5A5A"],
            [0.3, "#ff6e40"],
            [0.5, "#1E1E2D"],
            [0.7, "#3DD598"],
            [1, "#00c853"],
        ],
        text=[df["5D Momentum %"].tolist(), df["30D Momentum %"].tolist()],
        texttemplate="%{text:.1f}%",
        textfont={"size": 14, "color": "#E0E0E8"},
        hovertemplate="Sector: %{x}<br>Period: %{y}<br>Momentum: %{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- War-Economy Tilt Classification ---
    st.markdown(
        '<div class="section-header"><h3>War-Economy Sector Classification</h3></div>',
        unsafe_allow_html=True
    )

    beneficiaries = df[df["War Tilt"] == "BENEFICIARY"]
    victims = df[df["War Tilt"] == "VICTIM"]
    neutral = df[df["War Tilt"] == "NEUTRAL"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="tilt-card beneficiary">'
            '<div style="color:#3DD598;font-weight:700;font-size:0.9rem;margin-bottom:10px;">'
            '\U0001f4c8 War Beneficiaries</div>',
            unsafe_allow_html=True
        )
        for _, row in beneficiaries.iterrows():
            arrow = "\u2191" if row["30D Momentum %"] > 0 else "\u2193"
            color = "#3DD598" if row["30D Momentum %"] > 0 else "#FC5A5A"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid #1E1E2D;">'
                f'<span style="color:#E0E0E8;font-weight:500;">{row["Sector"]}</span>'
                f'<span style="color:{color};font-family:JetBrains Mono,monospace;'
                f'font-weight:600;">{arrow} {row["30D Momentum %"]}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(
            '<div class="tilt-card victim">'
            '<div style="color:#FC5A5A;font-weight:700;font-size:0.9rem;margin-bottom:10px;">'
            '\U0001f4c9 War Victims</div>',
            unsafe_allow_html=True
        )
        for _, row in victims.iterrows():
            arrow = "\u2191" if row["30D Momentum %"] > 0 else "\u2193"
            color = "#3DD598" if row["30D Momentum %"] > 0 else "#FC5A5A"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid #1E1E2D;">'
                f'<span style="color:#E0E0E8;font-weight:500;">{row["Sector"]}</span>'
                f'<span style="color:{color};font-family:JetBrains Mono,monospace;'
                f'font-weight:600;">{arrow} {row["30D Momentum %"]}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown(
            '<div class="tilt-card neutral">'
            '<div style="color:#5B8DEF;font-weight:700;font-size:0.9rem;margin-bottom:10px;">'
            '\u2696\ufe0f Neutral Sectors</div>',
            unsafe_allow_html=True
        )
        for _, row in neutral.iterrows():
            arrow = "\u2191" if row["30D Momentum %"] > 0 else "\u2193"
            color = "#3DD598" if row["30D Momentum %"] > 0 else "#FC5A5A"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:6px 0;'
                f'border-bottom:1px solid #1E1E2D;">'
                f'<span style="color:#E0E0E8;font-weight:500;">{row["Sector"]}</span>'
                f'<span style="color:{color};font-family:JetBrains Mono,monospace;'
                f'font-weight:600;">{arrow} {row["30D Momentum %"]}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
