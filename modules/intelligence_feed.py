"""MODULE 7 — COMMAND CENTER — Stockin UI Kit Style"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS
from data.fetchers import fetch_batch_prices, fetch_conflict_news, fetch_etf_data
from modules.geopolitical_tracker import _compute_conflict_intensity, _war_signal
from utils.styling import category_badge


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
    # --- War Signal ---
    news = fetch_conflict_news()
    intensity = _compute_conflict_intensity(news)
    signal = _war_signal(intensity)
    sig = {"GREEN": ("🟢", "#3DD598", "ACCUMULATE"), "AMBER": ("🟡", "#FFC542", "HOLD"),
           "RED": ("🔴", "#FC5A5A", "REDUCE RISK")}
    emoji, color, action = sig[signal]

    # --- Header ---
    hcol1, hcol2 = st.columns([3, 1])
    with hcol1:
        st.markdown("# My Portfolio")
        st.caption(f"War-Era ETF Command Center | {len(WAR_ECONOMY_ETFS)} ETFs Tracked")
    with hcol2:
        st.markdown(
            f'<div style="text-align:right;padding-top:10px;">'
            f'<span style="background:{color}18;color:{color};padding:6px 18px;border-radius:8px;'
            f'font-weight:600;font-size:0.85rem;">{emoji} {signal} — {action}</span></div>',
            unsafe_allow_html=True
        )

    # --- Fetch all prices ---
    all_tickers = tuple(WAR_ECONOMY_ETFS.keys())
    batch = _get_prices(all_tickers)
    prices = {}
    for ticker, meta in WAR_ECONOMY_ETFS.items():
        p = batch.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})
        prices[ticker] = {**meta, **p}

    active = {k: v for k, v in prices.items() if v.get("price", 0) > 0}
    if not active:
        st.error("No price data. Switch to Historical mode in sidebar.")
        return

    sorted_prices = sorted(active.items(), key=lambda x: x[1].get("change_pct", 0), reverse=True)

    # --- Portfolio Cards (Top 5 — like the UI kit) ---
    top5 = sorted_prices[:5]
    cols = st.columns(5)
    period = st.session_state.get("hist_period", "1y")

    for i, (ticker, data) in enumerate(top5):
        delta = data["change_pct"]
        chg_class = "change-up" if delta >= 0 else "change-down"
        sign = "+" if delta >= 0 else ""

        # Mini sparkline data
        df = fetch_etf_data(ticker, "3mo")
        spark_svg = ""
        if not df.empty and "Close" in df.columns:
            close = df["Close"].dropna().tolist()
            if len(close) > 5:
                mn, mx = min(close), max(close)
                rng = mx - mn if mx != mn else 1
                pts = []
                step = max(1, len(close) // 30)
                sampled = close[::step]
                for j, v in enumerate(sampled):
                    x = j * (120 / max(len(sampled)-1, 1))
                    y = 30 - ((v - mn) / rng) * 28
                    pts.append(f"{x:.1f},{y:.1f}")
                path = " ".join(pts)
                line_color = "#3DD598" if close[-1] >= close[0] else "#FC5A5A"
                spark_svg = (f'<svg width="120" height="32" style="margin:8px 0;">'
                             f'<polyline points="{path}" fill="none" stroke="{line_color}" stroke-width="1.8"/>'
                             f'</svg>')

        with cols[i]:
            st.markdown(
                f'<div class="portfolio-card">'
                f'<div class="category">{data["category"]}</div>'
                f'<div class="name">{data["name"][:22]}</div>'
                f'{spark_svg}'
                f'<div class="price">₹{data["price"]:,.2f}</div>'
                f'<span class="{chg_class} change">{sign}{delta:.2f}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Main Chart + Favorites Sidebar ---
    chart_col, fav_col = st.columns([3, 1])

    with chart_col:
        # Chart header with period pills
        st.markdown("### Performance Chart")
        fig = go.Figure()
        has_chart = False
        chart_colors = ["#5B8DEF", "#3DD598", "#FFC542", "#FC5A5A", "#AC6AFF", "#79C0FF"]

        for idx, (ticker, data) in enumerate(sorted_prices[:6]):
            df = fetch_etf_data(ticker, period)
            if not df.empty and "Close" in df.columns:
                close = df["Close"].dropna()
                if len(close) > 1 and float(close.iloc[0]) > 0:
                    has_chart = True
                    norm = (close / close.iloc[0]) * 100
                    fig.add_trace(go.Scatter(
                        x=close.index, y=norm,
                        name=WAR_ECONOMY_ETFS[ticker]["name"][:20],
                        mode="lines", line=dict(width=2.5, color=chart_colors[idx % len(chart_colors)]),
                    ))

        if has_chart:
            fig.update_layout(
                template="plotly_dark", height=400,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
                yaxis_title="Base 100",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10, color="#8B8B9E")),
                margin=dict(l=50, r=10, t=20, b=40),
                xaxis=dict(gridcolor="#1E1E2D", showgrid=True, zeroline=False),
                yaxis=dict(gridcolor="#1E1E2D", showgrid=True, zeroline=False),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#16161F", bordercolor="#2A2A3D"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with fav_col:
        st.markdown("### My Favorites")
        # Show top performers as favorite list
        for ticker, data in sorted_prices[:8]:
            delta = data["change_pct"]
            color = "#3DD598" if delta >= 0 else "#FC5A5A"
            sign = "+" if delta >= 0 else ""
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:10px 0;border-bottom:1px solid #1E1E2D;">'
                f'<div>'
                f'<div style="color:#E0E0E8;font-weight:600;font-size:0.85rem;">{data["name"][:18]}</div>'
                f'<div style="color:#6B6B80;font-size:0.72rem;">{data["category"]}</div>'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<div style="color:#F0F0F5;font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:600;">₹{data["price"]:,.2f}</div>'
                f'<div style="color:{color};font-family:JetBrains Mono,monospace;font-size:0.78rem;">{sign}{delta:.2f}%</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Market Trend (Full table — like UI kit) ---
    st.markdown("### Market Trend")

    # Category filter pills
    categories = sorted(set(v["category"] for v in active.values()))
    all_cats = ["All"] + categories

    if "selected_cat" not in st.session_state:
        st.session_state.selected_cat = "All"

    cat_cols = st.columns(min(len(all_cats), 10))
    for i, cat in enumerate(all_cats[:10]):
        with cat_cols[i]:
            if st.button(cat, key=f"cat_{cat}", use_container_width=True,
                        type="primary" if st.session_state.selected_cat == cat else "secondary"):
                st.session_state.selected_cat = cat
                st.rerun()

    filtered = sorted_prices if st.session_state.selected_cat == "All" else \
        [(t, d) for t, d in sorted_prices if d["category"] == st.session_state.selected_cat]

    # Table header
    st.markdown(
        '<div style="display:flex;padding:8px 18px;color:#6B6B80;font-size:0.72rem;'
        'font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">'
        '<div style="flex:2;">Name</div>'
        '<div style="flex:1;text-align:right;">Price</div>'
        '<div style="flex:1;text-align:right;">Change</div>'
        '<div style="flex:1;text-align:right;">War Score</div>'
        '</div>',
        unsafe_allow_html=True
    )

    for ticker, data in filtered:
        delta = data["change_pct"]
        color = "#3DD598" if delta >= 0 else "#FC5A5A"
        sign = "+" if delta >= 0 else ""
        badge = category_badge(data["category"])
        war_dots = "●" * data["war_score"] + "○" * (10 - data["war_score"])

        st.markdown(
            f'<div class="market-row">'
            f'<div class="etf-name">{data["name"]} {badge}</div>'
            f'<div class="etf-price">₹{data["price"]:,.2f}</div>'
            f'<div class="etf-change" style="color:{color};">{sign}{delta:.2f}%</div>'
            f'<div class="etf-return" style="color:#FFC542;font-size:0.7rem;">{war_dots}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- News ---
    st.markdown("### Conflict Intelligence")
    if news:
        ncols = st.columns(2)
        for i, article in enumerate(news[:6]):
            with ncols[i % 2]:
                st.markdown(
                    f'<div class="news-item">'
                    f'<div style="color:#E0E0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">{article["title"][:80]}</div>'
                    f'<div style="color:#6B6B80;font-size:0.75rem;">{article["source"]} '
                    f'{category_badge(article["keyword"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # --- Insight ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    top = sorted_prices[0][1] if sorted_prices else {}
    bot = sorted_prices[-1][1] if sorted_prices else {}
    insights = {
        "RED": f"Elevated conflict risk. {top.get('name','N/A')} leading — increase Gold/Defence.",
        "AMBER": f"Moderate tension. {top.get('name','N/A')} benefiting from war-economy flows. Hold SIP.",
        "GREEN": f"Baseline conflict. Continue SIP. {top.get('name','N/A')} strong — thesis intact.",
    }
    st.markdown(
        f'<div class="glass-card">'
        f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
        f'<span style="font-size:1.3em;">{emoji}</span>'
        f'<span style="color:#E0E0E8;font-weight:600;font-size:1rem;">AI Insight</span></div>'
        f'<p style="color:#A0A0B0;line-height:1.6;margin:0;">{insights[signal]}</p>'
        f'</div>',
        unsafe_allow_html=True
    )
