"""MODULE 1 — LIVE MARKET PULSE — Premium UI"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS
from data.fetchers import fetch_batch_prices, fetch_volume_signal, fetch_etf_data
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
    st.markdown("## Live Market Pulse")
    mode = st.session_state.get("data_mode", "Live (Today)")
    st.caption(f"{'Auto-refreshes every 60s' if mode == 'Live (Today)' else 'Historical mode'} | {len(WAR_ECONOMY_ETFS)} ETFs tracked")

    all_etfs = sorted(WAR_ECONOMY_ETFS.items(), key=lambda x: x[1]["war_score"], reverse=True)
    all_tickers = tuple(t for t, _ in all_etfs)
    batch = _get_prices(all_tickers)

    rows = []
    volume_alerts = []

    for ticker, meta in all_etfs:
        price_data = batch.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})
        if price_data["price"] == 0:
            continue
        vol_data = fetch_volume_signal(ticker)
        delta = price_data["change_pct"]

        rows.append({
            "Status": "🟢" if delta > 0 else ("🔴" if delta < 0 else "⚪"),
            "ETF": meta["name"],
            "Category": meta["category"],
            "Price (₹)": price_data["price"],
            "Change %": delta,
            "War Score": meta["war_score"],
            "Vol Spike": "⚠️" if vol_data["spike"] else "",
        })
        if vol_data["spike"]:
            volume_alerts.append(f"**{meta['name']}** — Volume {vol_data['ratio']}x avg")

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df, use_container_width=True, hide_index=True, height=min(len(rows) * 40 + 40, 600),
            column_config={
                "Change %": st.column_config.NumberColumn(format="%+.2f%%"),
                "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "War Score": st.column_config.ProgressColumn(min_value=0, max_value=10),
            }
        )
    else:
        st.warning("No data available. Try Historical mode.")

    # Volume alerts
    if volume_alerts:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.error("**Volume Spike Alerts (>2x 20-day avg)**")
        for a in volume_alerts:
            st.markdown(f"- {a}")

    # --- Mini Sparklines ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Price Trends")
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
        color = "#00e676" if is_up else "#ff1744"
        fill = "rgba(0,230,118,0.06)" if is_up else "rgba(255,23,68,0.06)"

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
