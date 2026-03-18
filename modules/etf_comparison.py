"""MODULE 3 — ETF PERFORMANCE COMPARISON ENGINE — Premium UI"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS, DEFAULT_COMPARISON
from data.fetchers import fetch_etf_data, calculate_returns, calculate_max_drawdown, sip_simulator


def render():
    st.markdown("## ETF Comparison Engine")
    st.caption("Compare, analyze, and simulate SIP returns across war-economy ETFs")

    etf_options = {f"{v['name']} ({k.replace('.NS','')})": k for k, v in WAR_ECONOMY_ETFS.items()}

    # Set defaults from config
    default_keys = []
    for k, v in etf_options.items():
        if v in DEFAULT_COMPARISON:
            default_keys.append(k)

    selected = st.multiselect(
        "Select ETFs to compare (2-5)",
        options=list(etf_options.keys()),
        default=default_keys[:5],
        max_selections=5,
    )

    if len(selected) < 2:
        st.warning("Select at least 2 ETFs to compare.")
        return

    col_period, col_spacer = st.columns([1, 3])
    with col_period:
        period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "3Y": "3y", "5Y": "5y"}
        period_label = st.selectbox("Period", list(period_map.keys()), index=3)
    period = period_map[period_label]

    tickers = [etf_options[s] for s in selected]

    with st.spinner("Fetching data..."):
        data = {t: fetch_etf_data(t, period) for t in tickers}

    # --- Normalized Chart ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### Normalized Performance (Base 100)")

    colors = ["#58a6ff", "#bc8cff", "#00e676", "#ffd740", "#ff6e7a", "#79c0ff"]
    fig = go.Figure()
    has_data = False

    for i, t in enumerate(tickers):
        df = data[t]
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 2 or float(close.iloc[0]) == 0:
            continue
        has_data = True
        normalized = (close / close.iloc[0]) * 100
        name = WAR_ECONOMY_ETFS[t]["name"]
        fig.add_trace(go.Scatter(
            x=close.index, y=normalized, name=name[:28],
            mode="lines", line=dict(width=2.5, color=colors[i % len(colors)]),
        ))

    if has_data:
        fig.update_layout(
            template="plotly_dark", height=480,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,17,23,0.8)",
            yaxis_title="Value (Base 100)", xaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10)),
            margin=dict(l=50, r=20, t=30, b=40),
            xaxis=dict(gridcolor="rgba(48,54,61,0.3)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.3)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data for selected ETFs. Try a different period or tickers.")

    # --- Return Table ---
    st.markdown("### Return Comparison")
    rows = []
    for t in tickers:
        df = data[t]
        if df.empty or "Close" not in df.columns:
            continue
        ret = calculate_returns(df)
        mdd = calculate_max_drawdown(df)
        meta = WAR_ECONOMY_ETFS[t]
        rows.append({
            "ETF": meta["name"],
            "Category": meta["category"],
            "1D": ret["1d"],
            "1W": ret["1w"],
            "1M": ret["1m"],
            "6M": ret["6m"],
            "1Y": ret["1y"],
            "CAGR": ret["cagr_3y"],
            "Max DD": mdd,
            "War Score": meta["war_score"],
        })
    if rows:
        rdf = pd.DataFrame(rows)
        st.dataframe(
            rdf, use_container_width=True, hide_index=True,
            column_config={
                "1D": st.column_config.NumberColumn(format="%.2f%%"),
                "1W": st.column_config.NumberColumn(format="%.2f%%"),
                "1M": st.column_config.NumberColumn(format="%.2f%%"),
                "6M": st.column_config.NumberColumn(format="%.2f%%"),
                "1Y": st.column_config.NumberColumn(format="%.2f%%"),
                "CAGR": st.column_config.NumberColumn(format="%.2f%%"),
                "Max DD": st.column_config.NumberColumn(format="%.2f%%"),
                "War Score": st.column_config.ProgressColumn(min_value=0, max_value=10),
            }
        )

    # --- Drawdown Chart ---
    st.markdown("### Drawdown Analysis")
    fig_dd = go.Figure()
    has_dd = False
    for i, t in enumerate(tickers):
        df = data[t]
        if df.empty or "Close" not in df.columns:
            continue
        close = df["Close"].dropna()
        if len(close) < 2:
            continue
        has_dd = True
        peak = close.expanding(min_periods=1).max()
        drawdown = ((close - peak) / peak) * 100
        fig_dd.add_trace(go.Scatter(
            x=close.index, y=drawdown, name=WAR_ECONOMY_ETFS[t]["name"][:25],
            fill="tozeroy", mode="lines",
            line=dict(width=1.5, color=colors[i % len(colors)]),
        ))
    if has_dd:
        fig_dd.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(13,17,23,0.8)",
            yaxis_title="Drawdown %", margin=dict(l=50, r=20, t=20, b=40),
            xaxis=dict(gridcolor="rgba(48,54,61,0.3)"),
            yaxis=dict(gridcolor="rgba(48,54,61,0.3)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    # --- SIP Simulator ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### SIP Return Simulator")

    sc1, sc2 = st.columns(2)
    with sc1:
        sip_etf = st.selectbox("Select ETF for SIP", selected)
        sip_ticker = etf_options[sip_etf]
    with sc2:
        sip_amount = st.number_input("Monthly SIP (₹)", 500, 100000, 5000, 500)

    sip_data = fetch_etf_data(sip_ticker, period="5y")
    if not sip_data.empty and "Close" in sip_data.columns:
        result = sip_simulator(sip_data, sip_amount)
        profit = result["current_value"] - result["invested"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Invested", f"₹{result['invested']:,.0f}")
        c2.metric("Current Value", f"₹{result['current_value']:,.0f}")
        c3.metric("Profit/Loss", f"₹{profit:,.0f}", delta=f"{result['return_pct']:.1f}%")
        c4.metric("Units", f"{result['units']:.2f}")
    else:
        st.info("Insufficient data for SIP simulation.")
