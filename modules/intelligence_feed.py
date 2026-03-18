"""MODULE 7 -- COMMAND CENTER -- Stockin UI Kit Style"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS
from data.fetchers import fetch_batch_prices, fetch_conflict_news, fetch_etf_data, get_cached_with_age
from modules.geopolitical_tracker import _compute_conflict_intensity, _war_signal
from utils.styling import category_badge, data_source_badge


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


def _make_sparkline_svg(close_list, width=120, height=32):
    """Generate inline SVG sparkline from close prices."""
    if len(close_list) < 3:
        return ""
    mn, mx = min(close_list), max(close_list)
    rng = mx - mn if mx != mn else 1
    step = max(1, len(close_list) // 30)
    sampled = close_list[::step]
    pts = []
    for j, v in enumerate(sampled):
        x = j * (width / max(len(sampled) - 1, 1))
        y = height - 2 - ((v - mn) / rng) * (height - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    line_color = "#3DD598" if close_list[-1] >= close_list[0] else "#FC5A5A"
    return (f'<svg width="{width}" height="{height}" style="margin:4px 0;">'
            f'<polyline points="{path}" fill="none" stroke="{line_color}" '
            f'stroke-width="1.8" stroke-linecap="round"/></svg>')


def render():
    # --- War Signal ---
    news = fetch_conflict_news()
    intensity = _compute_conflict_intensity(news)
    signal = _war_signal(intensity)
    sig = {"GREEN": ("\U0001f7e2", "#3DD598", "ACCUMULATE"),
           "AMBER": ("\U0001f7e1", "#FFC542", "HOLD"),
           "RED": ("\U0001f534", "#FC5A5A", "REDUCE RISK")}
    emoji, color, action = sig[signal]

    # --- Header Bar ---
    source = st.session_state.get("last_data_source", "yfinance")
    st.markdown(
        f'<div class="dashboard-header">'
        f'<div class="header-left">'
        f'<span style="color:#F0F0F5;font-weight:700;font-size:1.4rem;">My Portfolio</span>'
        f'</div>'
        f'<div class="header-right">'
        f'{data_source_badge(source)}'
        f'<span style="background:{color}18;color:{color};padding:6px 16px;border-radius:8px;'
        f'font-weight:600;font-size:0.82rem;">{emoji} {signal} \u2014 {action}</span>'
        f'<div class="header-avatar">JM</div>'
        f'</div></div>',
        unsafe_allow_html=True
    )
    st.caption(f"War-Era ETF Command Center | {len(WAR_ECONOMY_ETFS)} ETFs Tracked")

    # --- Fetch all prices ---
    all_tickers = tuple(WAR_ECONOMY_ETFS.keys())
    batch = _get_prices(all_tickers)
    prices = {}
    for ticker, meta in WAR_ECONOMY_ETFS.items():
        p = batch.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})
        prices[ticker] = {**meta, **p}

    active = {k: v for k, v in prices.items() if v.get("price", 0) > 0}

    # --- Fallback card if no data ---
    if not active:
        # Show cached data with age
        cache_info = []
        for t in list(WAR_ECONOMY_ETFS.keys())[:5]:
            cached, hours = get_cached_with_age(t)
            if cached["price"] > 0:
                cache_info.append((t, cached, hours))

        if cache_info:
            st.markdown(
                '<div class="fallback-card">'
                '<div class="fb-icon">\u26a0\ufe0f</div>'
                '<div>'
                '<div style="color:#FFC542;font-weight:600;margin-bottom:4px;">Using Cached Data</div>'
                '<div class="fb-text">Live data sources unavailable. Showing last known prices.</div>'
                '</div></div>',
                unsafe_allow_html=True
            )
            for t, cached, hours in cache_info:
                name = WAR_ECONOMY_ETFS[t]["name"]
                age_str = f"{hours:.0f}h ago" if hours < 24 else f"{hours/24:.0f}d ago"
                st.markdown(
                    f'<div class="market-row">'
                    f'<div class="etf-info"><div class="etf-name">{name}</div>'
                    f'<div class="etf-cat">Cached {age_str}</div></div>'
                    f'<div class="etf-price fb-price">\u20b9{cached["price"]:,.2f}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            if st.button("Retry Data Fetch", type="primary"):
                st.cache_data.clear()
                st.rerun()
        else:
            st.error("No price data available. Switch to Historical mode in sidebar.")
        return

    sorted_prices = sorted(active.items(), key=lambda x: x[1].get("change_pct", 0), reverse=True)

    # --- Portfolio Cards (Top 5 -- v2 design) ---
    top5 = sorted_prices[:5]
    cols = st.columns(5)
    period = st.session_state.get("hist_period", "1y")
    category_icons = {
        "Defence": "\U0001f6e1\ufe0f", "Defence/PSU": "\U0001f3ed",
        "Gold": "\U0001f947", "Silver": "\U0001fa99",
        "PSU Bank": "\U0001f3e6", "Infrastructure": "\U0001f3d7\ufe0f",
        "Nifty 50": "\U0001f4c8", "Nifty Next 50": "\U0001f4ca",
        "Midcap": "\U0001f680", "Midcap 150": "\U0001f680",
        "Banking": "\U0001f4b3", "IT": "\U0001f4bb",
        "Pharma": "\U0001f48a", "US Tech": "\U0001f30d",
    }

    for i, (ticker, data) in enumerate(top5):
        delta = data["change_pct"]
        sign = "+" if delta >= 0 else ""
        delta_bg = "#3DD59818" if delta >= 0 else "#FC5A5A18"
        delta_color = "#3DD598" if delta >= 0 else "#FC5A5A"
        icon = category_icons.get(data["category"], "\U0001f4c8")

        # Mini sparkline
        df = fetch_etf_data(ticker, "3mo")
        spark_svg = ""
        if not df.empty and "Close" in df.columns:
            close = df["Close"].dropna().tolist()
            if len(close) > 5:
                spark_svg = _make_sparkline_svg(close)

        with cols[i]:
            st.markdown(
                f'<div class="portfolio-card-v2">'
                f'<div class="card-icon">{icon}</div>'
                f'<div class="delta-badge" style="background:{delta_bg};color:{delta_color};">'
                f'{sign}{delta:.2f}%</div>'
                f'<div style="color:#E0E0E8;font-weight:600;font-size:0.9rem;margin-bottom:2px;">'
                f'{data["name"][:20]}</div>'
                f'{spark_svg}'
                f'<div class="meta-row">'
                f'<div><div class="meta-label">Total Share</div>'
                f'<div class="meta-value">\u20b9{data["price"]:,.2f}</div></div>'
                f'<div style="text-align:right;"><div class="meta-label">Total Return</div>'
                f'<div class="meta-value" style="color:{delta_color};">{sign}{delta:.2f}%</div></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Main Chart + Favorites Sidebar ---
    chart_col, fav_col = st.columns([3, 1])

    with chart_col:
        st.markdown(
            '<div class="section-header">'
            '<h3>Performance Chart</h3>'
            '</div>',
            unsafe_allow_html=True
        )

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
                template="plotly_dark", height=420,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
                yaxis_title="Base 100",
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                           font=dict(size=10, color="#8B8B9E")),
                margin=dict(l=50, r=10, t=20, b=40),
                xaxis=dict(gridcolor="#1E1E2D", showgrid=True, zeroline=False),
                yaxis=dict(gridcolor="#1E1E2D", showgrid=True, zeroline=False),
                hovermode="x unified",
                hoverlabel=dict(bgcolor="#16161F", bordercolor="#2A2A3D",
                               font=dict(family="JetBrains Mono", size=12)),
            )
            st.plotly_chart(fig, use_container_width=True)

    with fav_col:
        st.markdown(
            '<div class="section-header">'
            '<h3>My Favorites</h3>'
            '<span class="see-all">See All</span>'
            '</div>',
            unsafe_allow_html=True
        )
        for ticker, data in sorted_prices[:8]:
            delta = data["change_pct"]
            d_color = "#3DD598" if delta >= 0 else "#FC5A5A"
            sign = "+" if delta >= 0 else ""
            icon = category_icons.get(data["category"], "\U0001f4c8")

            st.markdown(
                f'<div class="fav-item">'
                f'<div class="fav-left">'
                f'<div class="fav-icon">{icon}</div>'
                f'<div><div class="fav-name">{data["name"][:18]}</div>'
                f'<div class="fav-cat">{data["category"]}</div></div>'
                f'</div>'
                f'<div>'
                f'<div class="fav-price">\u20b9{data["price"]:,.2f}</div>'
                f'<div class="fav-delta" style="color:{d_color};">{sign}{delta:.2f}%</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Market Trend ---
    st.markdown(
        '<div class="section-header">'
        '<h3>Market Trend</h3>'
        '<span class="see-all">See All</span>'
        '</div>',
        unsafe_allow_html=True
    )

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
        '<div style="display:flex;padding:8px 18px;color:#6B6B80;font-size:0.7rem;'
        'font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">'
        '<div style="width:32px;margin-right:12px;"></div>'
        '<div style="flex:2;">Name</div>'
        '<div style="flex:1;text-align:right;">Price</div>'
        '<div style="flex:1;text-align:right;">Change</div>'
        '<div style="flex:1;text-align:right;">Chart</div>'
        '<div style="flex:0.8;text-align:right;">War Score</div>'
        '</div>',
        unsafe_allow_html=True
    )

    for ticker, data in filtered:
        delta = data["change_pct"]
        d_color = "#3DD598" if delta >= 0 else "#FC5A5A"
        sign = "+" if delta >= 0 else ""
        icon = category_icons.get(data["category"], "\U0001f4c8")
        war_dots = "\u25cf" * data["war_score"] + "\u25cb" * (10 - data["war_score"])

        # Mini sparkline for table row
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
            f'<div class="etf-name">{data["name"]}</div>'
            f'<div class="etf-cat">{data["category"]}</div></div>'
            f'<div class="etf-price">\u20b9{data["price"]:,.2f}</div>'
            f'<div class="etf-change" style="color:{d_color};">{sign}{delta:.2f}%</div>'
            f'<div class="etf-spark">{spark}</div>'
            f'<div class="etf-score">{war_dots}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- Conflict Intelligence ---
    st.markdown(
        '<div class="section-header">'
        '<h3>Conflict Intelligence</h3>'
        '</div>',
        unsafe_allow_html=True
    )
    if news:
        high_kw = ["strike", "attack", "bomb", "invasion", "nuclear", "missile", "escalat"]
        med_kw = ["tension", "military", "deploy", "sanction", "threat"]
        ncols = st.columns(2)
        for i, article in enumerate(news[:6]):
            title_lower = article["title"].lower()
            severity = "high" if any(k in title_lower for k in high_kw) else \
                       ("medium" if any(k in title_lower for k in med_kw) else "low")
            with ncols[i % 2]:
                st.markdown(
                    f'<div class="news-item-accent {severity}">'
                    f'<div style="color:#E0E0E8;font-weight:600;font-size:0.88rem;margin-bottom:4px;">'
                    f'{article["title"][:80]}</div>'
                    f'<div style="color:#6B6B80;font-size:0.75rem;">{article["source"]} '
                    f'{category_badge(article["keyword"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # --- AI Insight ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    top = sorted_prices[0][1] if sorted_prices else {}
    insights = {
        "RED": f"Elevated conflict risk. {top.get('name','N/A')} leading \u2014 increase Gold/Defence.",
        "AMBER": f"Moderate tension. {top.get('name','N/A')} benefiting from war-economy flows. Hold SIP.",
        "GREEN": f"Baseline conflict. Continue SIP. {top.get('name','N/A')} strong \u2014 thesis intact.",
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
