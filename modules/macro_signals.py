"""MODULE 5 — MACRO SIGNAL DASHBOARD — Premium UI"""
import streamlit as st
import plotly.graph_objects as go
from config import MACRO, ALERTS
from data.fetchers import fetch_macro_data, fetch_etf_data


def _sparkline(ticker: str, period: str = "1mo", color: str = "#58a6ff"):
    df = fetch_etf_data(ticker, period)
    if df.empty or "Close" not in df.columns:
        return None
    close = df["Close"].dropna()
    if len(close) < 2:
        return None
    is_up = float(close.iloc[-1]) >= float(close.iloc[0])
    line_color = "#00e676" if is_up else "#ff1744"
    fig = go.Figure(go.Scatter(
        x=close.index, y=close, mode="lines",
        line=dict(color=line_color, width=1.5),
        fill="tozeroy", fillcolor=f"{'rgba(0,230,118,0.08)' if is_up else 'rgba(255,23,68,0.08)'}",
    ))
    fig.update_layout(
        template="plotly_dark", height=70,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def render():
    st.markdown("## Macro Signal Dashboard")
    st.caption("Global macro indicators with threshold alerts")

    macro = fetch_macro_data()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gold = macro.get("gold_usd", {})
        st.metric("Gold (USD/oz)", f"${gold.get('price', 0):,.0f}",
                  delta=f"{gold.get('change_pct', 0):.2f}%")
        fig = _sparkline(MACRO["gold_usd"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_gold")

    with col2:
        silver = macro.get("silver_usd", {})
        st.metric("Silver (USD/oz)", f"${silver.get('price', 0):,.1f}",
                  delta=f"{silver.get('change_pct', 0):.2f}%")
        fig = _sparkline(MACRO["silver_usd"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_silver")

    with col3:
        usdinr = macro.get("usd_inr", {})
        st.metric("USD/INR", f"₹{usdinr.get('price', 0):.2f}",
                  delta=f"{usdinr.get('change_pct', 0):.2f}%", delta_color="inverse")
        fig = _sparkline(MACRO["usd_inr"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_usdinr")

    with col4:
        crude = macro.get("brent_crude", {})
        st.metric("Brent Crude", f"${crude.get('price', 0):.1f}",
                  delta=f"{crude.get('change_pct', 0):.2f}%")
        fig = _sparkline(MACRO["brent_crude"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_crude")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    col5, col6, col7 = st.columns(3)
    with col5:
        us10y = macro.get("us_10y", {})
        st.metric("US 10Y Yield", f"{us10y.get('price', 0):.2f}%",
                  delta=f"{us10y.get('change_pct', 0):.2f}%", delta_color="inverse")
    with col6:
        vix = macro.get("india_vix", {})
        st.metric("India VIX (Fear)", f"{vix.get('price', 0):.2f}",
                  delta=f"{vix.get('change_pct', 0):.2f}%", delta_color="inverse")
    with col7:
        nifty = macro.get("nifty50", {})
        st.metric("Nifty 50", f"{nifty.get('price', 0):,.0f}",
                  delta=f"{nifty.get('change_pct', 0):.2f}%")

    # --- Alerts ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Threshold Alerts")

    alerts_fired = []
    gold_p = macro.get("gold_usd", {}).get("price", 0)
    vix_p = macro.get("india_vix", {}).get("price", 0)
    crude_p = macro.get("brent_crude", {}).get("price", 0)
    usdinr_p = macro.get("usd_inr", {}).get("price", 0)

    if gold_p > ALERTS["gold_usd_high"]:
        alerts_fired.append(f"Gold ${gold_p:,.0f} > ${ALERTS['gold_usd_high']:,} — Defence + Gold tilt signal ACTIVE")
    if vix_p > ALERTS["india_vix_high"]:
        alerts_fired.append(f"India VIX {vix_p:.1f} > {ALERTS['india_vix_high']} — Fear elevated, increase Gold")
    if crude_p > ALERTS["crude_high"]:
        alerts_fired.append(f"Brent ${crude_p:.1f} > ${ALERTS['crude_high']} — India CAD pressure")
    if usdinr_p > ALERTS["usd_inr_high"]:
        alerts_fired.append(f"USD/INR ₹{usdinr_p:.2f} > ₹{ALERTS['usd_inr_high']} — Rupee weak, Gold hedge ON")

    if alerts_fired:
        for a in alerts_fired:
            st.error(f"**ALERT:** {a}")
    else:
        st.success("All macro indicators within normal thresholds.")
