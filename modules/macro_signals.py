"""MODULE 5 -- MACRO SIGNAL DASHBOARD -- Premium UI"""
import streamlit as st
import plotly.graph_objects as go
from config import MACRO, ALERTS
from data.fetchers import fetch_macro_data, fetch_etf_data
from utils.styling import data_source_badge


def _sparkline(ticker: str, period: str = "1mo", color: str = "#58a6ff"):
    df = fetch_etf_data(ticker, period)
    if df.empty or "Close" not in df.columns:
        return None
    close = df["Close"].dropna()
    if len(close) < 2:
        return None
    is_up = float(close.iloc[-1]) >= float(close.iloc[0])
    line_color = "#3DD598" if is_up else "#FC5A5A"
    fig = go.Figure(go.Scatter(
        x=close.index, y=close, mode="lines",
        line=dict(color=line_color, width=1.5),
        fill="tozeroy", fillcolor=f"{'rgba(61,213,152,0.08)' if is_up else 'rgba(252,90,90,0.08)'}",
    ))
    fig.update_layout(
        template="plotly_dark", height=70,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def _stat_card_html(label: str, value: str, change_pct: float, trend_label: str = "trend title") -> str:
    """Render a stat card matching the Views All UI kit style."""
    trend_class = "up" if change_pct >= 0 else "down"
    sign = "+" if change_pct >= 0 else ""
    return (
        f'<div class="stat-card">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<span style="color:#6B6B80;font-size:0.72rem;">{trend_label}</span>'
        f'<span class="trend {trend_class}">{sign}{change_pct:.2f}%</span>'
        f'</div></div>'
    )


def render():
    source = st.session_state.get("last_data_source", "yfinance")
    st.markdown(
        f'<div class="dashboard-header">'
        f'<div class="header-left">'
        f'<span style="color:#F0F0F5;font-weight:700;font-size:1.4rem;">Macro Signals</span>'
        f'</div>'
        f'<div class="header-right">'
        f'{data_source_badge(source)}'
        f'<span style="color:#6B6B80;font-size:0.8rem;">Global indicators + threshold alerts</span>'
        f'</div></div>',
        unsafe_allow_html=True
    )

    macro = fetch_macro_data()

    # --- Top 4 stat cards with sparklines ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        gold = macro.get("gold_usd", {})
        st.markdown(_stat_card_html(
            "Gold (USD/oz)", f"${gold.get('price', 0):,.0f}",
            gold.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
        fig = _sparkline(MACRO["gold_usd"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_gold")

    with col2:
        silver = macro.get("silver_usd", {})
        st.markdown(_stat_card_html(
            "Silver (USD/oz)", f"${silver.get('price', 0):,.1f}",
            silver.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
        fig = _sparkline(MACRO["silver_usd"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_silver")

    with col3:
        usdinr = macro.get("usd_inr", {})
        st.markdown(_stat_card_html(
            "USD/INR", f"\u20b9{usdinr.get('price', 0):.2f}",
            -usdinr.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
        fig = _sparkline(MACRO["usd_inr"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_usdinr")

    with col4:
        crude = macro.get("brent_crude", {})
        st.markdown(_stat_card_html(
            "Brent Crude", f"${crude.get('price', 0):.1f}",
            crude.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
        fig = _sparkline(MACRO["brent_crude"])
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="sp_crude")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Bottom 3 stat cards ---
    col5, col6, col7 = st.columns(3)
    with col5:
        us10y = macro.get("us_10y", {})
        st.markdown(_stat_card_html(
            "US 10Y Yield", f"{us10y.get('price', 0):.2f}%",
            -us10y.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
    with col6:
        vix = macro.get("india_vix", {})
        st.markdown(_stat_card_html(
            "India VIX (Fear)", f"{vix.get('price', 0):.2f}",
            -vix.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)
    with col7:
        nifty = macro.get("nifty50", {})
        st.markdown(_stat_card_html(
            "Nifty 50", f"{nifty.get('price', 0):,.0f}",
            nifty.get("change_pct", 0), "1D change"
        ), unsafe_allow_html=True)

    # --- Alerts ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><h3>Threshold Alerts</h3></div>',
        unsafe_allow_html=True
    )

    alerts_fired = []
    gold_p = macro.get("gold_usd", {}).get("price", 0)
    vix_p = macro.get("india_vix", {}).get("price", 0)
    crude_p = macro.get("brent_crude", {}).get("price", 0)
    usdinr_p = macro.get("usd_inr", {}).get("price", 0)

    if gold_p > ALERTS["gold_usd_high"]:
        alerts_fired.append(f"Gold ${gold_p:,.0f} > ${ALERTS['gold_usd_high']:,} \u2014 Defence + Gold tilt signal ACTIVE")
    if vix_p > ALERTS["india_vix_high"]:
        alerts_fired.append(f"India VIX {vix_p:.1f} > {ALERTS['india_vix_high']} \u2014 Fear elevated, increase Gold")
    if crude_p > ALERTS["crude_high"]:
        alerts_fired.append(f"Brent ${crude_p:.1f} > ${ALERTS['crude_high']} \u2014 India CAD pressure")
    if usdinr_p > ALERTS["usd_inr_high"]:
        alerts_fired.append(f"USD/INR \u20b9{usdinr_p:.2f} > \u20b9{ALERTS['usd_inr_high']} \u2014 Rupee weak, Gold hedge ON")

    if alerts_fired:
        for a in alerts_fired:
            st.markdown(
                f'<div class="news-item-accent high">'
                f'<div style="color:#FC5A5A;font-weight:600;font-size:0.88rem;">'
                f'\u26a0\ufe0f ALERT: {a}</div></div>',
                unsafe_allow_html=True
            )
    else:
        st.success("All macro indicators within normal thresholds.")
