"""MODULE 4 — SECTOR ROTATION HEATMAP"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import SECTORS
from data.fetchers import fetch_sector_momentum


def render():
    st.header("Module 4 — Sector Rotation Heatmap")
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
        st.warning("Sector data unavailable — market may be closed or tickers not responding.")
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    # --- Heatmap ---
    fig = go.Figure(data=go.Heatmap(
        z=[df["5D Momentum %"].tolist(), df["30D Momentum %"].tolist()],
        x=df["Sector"].tolist(),
        y=["5-Day", "30-Day"],
        zmid=0,
        colorscale=[
            [0, "#ff1744"],
            [0.3, "#ff6e40"],
            [0.5, "#424242"],
            [0.7, "#69f0ae"],
            [1, "#00c853"],
        ],
        text=[df["5D Momentum %"].tolist(), df["30D Momentum %"].tolist()],
        texttemplate="%{text:.1f}%",
        textfont={"size": 14},
        hovertemplate="Sector: %{x}<br>Period: %{y}<br>Momentum: %{z:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- War-Economy Tilt Table ---
    st.subheader("War-Economy Sector Classification")

    beneficiaries = df[df["War Tilt"] == "BENEFICIARY"]
    victims = df[df["War Tilt"] == "VICTIM"]
    neutral = df[df["War Tilt"] == "NEUTRAL"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("**War Beneficiaries**")
        for _, row in beneficiaries.iterrows():
            arrow = "↑" if row["30D Momentum %"] > 0 else "↓"
            st.markdown(f"- **{row['Sector']}** {arrow} {row['30D Momentum %']}%")
    with col2:
        st.error("**War Victims**")
        for _, row in victims.iterrows():
            arrow = "↑" if row["30D Momentum %"] > 0 else "↓"
            st.markdown(f"- **{row['Sector']}** {arrow} {row['30D Momentum %']}%")
    with col3:
        st.info("**Neutral Sectors**")
        for _, row in neutral.iterrows():
            arrow = "↑" if row["30D Momentum %"] > 0 else "↓"
            st.markdown(f"- **{row['Sector']}** {arrow} {row['30D Momentum %']}%")

    st.dataframe(df, use_container_width=True, hide_index=True)
