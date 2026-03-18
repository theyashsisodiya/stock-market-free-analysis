"""MODULE 1 -- LIVE MARKET PULSE -- Premium UI"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS
from data.fetchers import fetch_batch_prices, fetch_volume_signal, fetch_etf_data
from utils.styling import category_badge, data_source_badge
from modules.intelligence_feed import _make_sparkline_svg


CATEGORY_ICONS = {
    "Defence": "\U0001f6e1\ufe0f", "Defence/PSU": "\U0001f3ed",
    "Gold": "\U0001f947", "Silver": "\U0001fa99",
    "PSU Bank": "\U0001f3e6", "Infrastructure": "\U0001f3d7\ufe0f",
    "Nifty 50": "\U0001f4c8", "Nifty Next 50": "\U0001f4ca",
    "Midcap": "\U0001f680", "Midcap 150": "\U0001f680",
    "Banking": "\U0001f4b3", "IT": "\U0001f4bb",
    "Pharma": "\U0001f48a", "US Tech": "\U0001f30d",
}


def _get_prices(tickers):
    mode = st.session_state.get("data_mode", "Live (Today)")
    if mode == "Live (Today)":
        batch = fetch_batch_prices(tickers)
        if any(v.get("price", 0) > 0 for v in batch.values()):
            return batch
    period = st.session_state.get("hist_period", "1y")
    results = {}
    for t in tickers:
        df = fetch_etf_data(t, period)
        if not df.empty and "Close" in df.columns:
            close = df["Close"].dropna()
            if len(close) >= 2:
                price, prev = float(close.iloc[-1]), float(close.iloc[-2])
                change = ((price - prev) / prev) * 100 if prev else 0
                results[t] = {"price": round(price, 2), "change_pct": round(change, 2), "prev_close": round(prev, 2)}
                continue
        results[t] = {"price": 0, "change_pct": 0, "prev_close": 0}
    return results


def render():
    # Header bar
    source = st.session_state.get("last_data_source", "yfinance")
    mode = st.session_state.get("data_mode", "Live (Today)")
    st.markdown(
        f'<div class="dashboard-header">'
        f'<div class="header-left">'
        f'<span style="color:#F0F0F5;font-weight:700;font-size:1.4rem;">Stock Market</span>'
        f'</div>'
        f'<div class="header-right">'
        f'{data_source_badge(source)}'
        f'<span style="color:#6B6B80;font-size:0.8rem;">'
        f'{"Auto-refreshes every 60s" if mode == "Live (Today)" else "Historical mode"}</span>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    st.caption(f"{len(WAR_ECONOMY_ETFS)} ETFs tracked | Sorted by War Score")

    all_etfs = sorted(WAR_ECONOMY_ETFS.items(), key=lambda x: x[1]["war_score"], reverse=True)
    all_tickers = tuple(t for t, _ in all_etfs)
    batch = _get_prices(all_tickers)

    # Category filter pills
    categories = sorted(set(v["category"] for _, v in all_etfs))
    all_cats = ["All"] + categories
    if "mp_cat" not in st.session_state:
        st.session_state.mp_cat = "All"

    cat_cols = st.columns(min(len(all_cats), 10))
    for i, cat in enumerate(all_cats[:10]):
        with cat_cols[i]:
            if st.button(cat, key=f"mp_cat_{cat}", use_container_width=True,
                        type="primary" if st.session_state.mp_cat == cat else "secondary"):
                st.session_state.mp_cat = cat
                st.rerun()

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Custom HTML Market Table ---
    volume_alerts = []

    # Table header
    st.markdown(
        '<div style="display:flex;padding:8px 18px;color:#6B6B80;font-size:0.7rem;'
        'font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">'
        '<div style="width:32px;margin-right:12px;"></div>'
        '<div style="flex:2;">Name</div>'
        '<div style="flex:1;text-align:right;">Price</div>'
        '<div style="flex:1;text-align:right;">Change</div>'
        '<div style="flex:1;text-align:right;">Chart</div>'
        '<div style="flex:0.8;text-align:right;">War Score</div>'
        '<div style="flex:0.5;text-align:center;">Vol</div>'
        '</div>',
        unsafe_allow_html=True
    )

    for ticker, meta in all_etfs:
        if st.session_state.mp_cat != "All" and meta["category"] != st.session_state.mp_cat:
            continue

        price_data = batch.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})
        if price_data["price"] == 0:
            continue

        vol_data = fetch_volume_signal(ticker)
        delta = price_data["change_pct"]
        d_color = "#3DD598" if delta >= 0 else "#FC5A5A"
        sign = "+" if delta >= 0 else ""
        icon = CATEGORY_ICONS.get(meta["category"], "\U0001f4c8")
        war_dots = "\u25cf" * meta["war_score"] + "\u25cb" * (10 - meta["war_score"])
        vol_icon = "\u26a0\ufe0f" if vol_data["spike"] else ""

        if vol_data["spike"]:
            volume_alerts.append(f"**{meta['name']}** \u2014 Volume {vol_data['ratio']}x avg")

        # Mini sparkline
        df = fetch_etf_data(ticker, "1mo")
        spark = ""
        if not df.empty and "Close" in df.columns:
            close = df["Close"].dropna().tolist()
            if len(close) > 3:
                spark = _make_sparkline_svg(close, width=80, height=24)

        st.markdown(
            f'<div class="market-row">'
            f'<div class="etf-icon">{icon}</div>'
            f'<div class="etf-info">'
            f'<div class="etf-name">{meta["name"]}</div>'
            f'<div class="etf-cat">{meta["category"]}</div></div>'
            f'<div class="etf-price">\u20b9{price_data["price"]:,.2f}</div>'
            f'<div class="etf-change" style="color:{d_color};">{sign}{delta:.2f}%</div>'
            f'<div class="etf-spark">{spark}</div>'
            f'<div class="etf-score">{war_dots}</div>'
            f'<div style="flex:0.5;text-align:center;font-size:0.9rem;">{vol_icon}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Volume alerts
    if volume_alerts:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.error("**Volume Spike Alerts (>2x 20-day avg)**")
        for a in volume_alerts:
            st.markdown(f"- {a}")

    # --- Price Trend Sparklines ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">'
        '<h3>Price Trends</h3>'
        '</div>',
        unsafe_allow_html=True
    )
    period = st.session_state.get("hist_period", "1y")

    chart_etfs = [(t, m) for t, m in all_etfs if batch.get(t, {}).get("price", 0) > 0][:8]
    cols = st.columns(4)

    for i, (ticker, meta) in enumerate(chart_etfs):
        df = fetch_etf_data(ticker, period)
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 2:
            continue
        is_up = float(close.iloc[-1]) >= float(close.iloc[0])
        color = "#3DD598" if is_up else "#FC5A5A"
        fill = "rgba(61,213,152,0.06)" if is_up else "rgba(252,90,90,0.06)"

        with cols[i % 4]:
            fig = go.Figure(go.Scatter(
                x=close.index, y=close, mode="lines",
                line=dict(color=color, width=2),
                fill="tozeroy", fillcolor=fill,
            ))
            fig.update_layout(
                template="plotly_dark", height=130,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,17,23,0.5)",
                margin=dict(l=5, r=5, t=28, b=5),
                title=dict(text=meta["name"][:22], font=dict(size=11, color="#c9d1d9")),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, key=f"spark_{ticker}")
