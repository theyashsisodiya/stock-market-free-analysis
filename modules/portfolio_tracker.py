"""MODULE 6 — PORTFOLIO TRACKER — Lumpsum + SIP + Multi-ETF Simulator"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config import WAR_ECONOMY_ETFS, PORTFOLIO_AGGRESSIVE, PORTFOLIO_ULTRA, PORTFOLIO_HEDGED
from data.fetchers import fetch_etf_data, calculate_returns, calculate_max_drawdown, sip_simulator
from utils.styling import format_inr, category_badge


def _render_portfolio_template(portfolio: dict):
    st.markdown(f'<div class="glass-card"><h3 style="margin-top:0;">{portfolio["name"]}</h3>', unsafe_allow_html=True)
    for ticker, alloc in portfolio["allocations"].items():
        meta = WAR_ECONOMY_ETFS.get(ticker, {})
        color = "#3DD598" if alloc["pct"] >= 25 else ("#FFC542" if alloc["pct"] >= 15 else "#5B8DEF")
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:10px 0;border-bottom:1px solid #1E1E2D;">'
            f'<div style="flex:2;">'
            f'<span style="color:#E0E0E8;font-weight:600;">{meta.get("name", ticker)}</span><br>'
            f'<span style="color:#6B6B80;font-size:0.78rem;">{alloc["reason"][:60]}</span></div>'
            f'<div style="flex:1;text-align:right;">'
            f'<span style="color:{color};font-family:JetBrains Mono,monospace;font-weight:700;font-size:1.1rem;">{alloc["pct"]}%</span><br>'
            f'<span style="color:#6B6B80;font-family:JetBrains Mono,monospace;font-size:0.8rem;">₹{alloc["amt"]:,}/mo</span>'
            f'</div></div>',
            unsafe_allow_html=True
        )
    c1, c2 = st.columns(2)
    c1.metric("Expected 3Y CAGR", portfolio["expected_cagr"], help="[FORECAST]")
    c2.metric("Max Drawdown", portfolio["max_drawdown"])
    st.caption(f"Rebalance: {portfolio['rebalance_trigger']}")
    st.markdown('</div>', unsafe_allow_html=True)


def _lumpsum_return(df, amount):
    """Calculate lumpsum return."""
    if df.empty or "Close" not in df.columns or len(df) < 2:
        return {"invested": amount, "current_value": amount, "return_pct": 0, "abs_return": 0}
    close = df["Close"].dropna()
    buy_price = float(close.iloc[0])
    curr_price = float(close.iloc[-1])
    if buy_price <= 0:
        return {"invested": amount, "current_value": amount, "return_pct": 0, "abs_return": 0}
    units = amount / buy_price
    current_value = units * curr_price
    return_pct = ((current_value / amount) - 1) * 100
    return {
        "invested": amount,
        "current_value": round(current_value, 2),
        "return_pct": round(return_pct, 2),
        "abs_return": round(current_value - amount, 2),
        "units": round(units, 4),
        "buy_price": round(buy_price, 2),
        "curr_price": round(curr_price, 2),
    }


def render():
    st.markdown("## Portfolio Tracker & Simulator")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Multi-ETF Simulator", "Lumpsum Calculator", "SIP Calculator", "Model Portfolios"
    ])

    etf_options = {f"{v['name']} ({k.replace('.NS','')})": k for k, v in WAR_ECONOMY_ETFS.items()}

    # ========================
    # TAB 1: MULTI-ETF SIMULATOR
    # ========================
    with tab1:
        st.markdown("### Invest ₹X Across Multiple ETFs — See Your Returns")
        st.caption("Select ETFs, set allocation %, enter total amount — get projected returns based on historical data")

        total_amount = st.number_input(
            "Total Investment Amount (₹)", min_value=1000, max_value=10000000,
            value=100000, step=10000, key="multi_total"
        )

        period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "3Y": "3y", "5Y": "5y"}
        pcol1, pcol2 = st.columns([1, 3])
        with pcol1:
            sim_period = st.selectbox("Period", list(period_map.keys()), index=3, key="sim_period")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Dynamic ETF selection
        if "sim_etfs" not in st.session_state:
            st.session_state.sim_etfs = 4

        sim_data = []
        total_pct = 0

        for i in range(st.session_state.sim_etfs):
            c1, c2, c3 = st.columns([4, 1, 1])
            # Default selections
            defaults = ["SILVERBEES.NS", "MODEFENCE.NS", "GOLDBEES.NS", "PSUBNKBEES.NS", "NIFTYBEES.NS"]
            default_pcts = [40, 30, 20, 10, 0]
            default_idx = 0
            default_pct = 25

            if i < len(defaults):
                default_key = next((k for k, v in etf_options.items() if v == defaults[i]), None)
                if default_key:
                    default_idx = list(etf_options.keys()).index(default_key)
                default_pct = default_pcts[i] if i < len(default_pcts) else 10

            with c1:
                etf = st.selectbox(f"ETF {i+1}", list(etf_options.keys()), index=default_idx, key=f"sim_etf_{i}")
            with c2:
                pct = st.number_input(f"Alloc %", 0, 100, default_pct, 5, key=f"sim_pct_{i}")
            with c3:
                amt = total_amount * pct / 100
                st.markdown(f'<div style="padding-top:28px;color:#E0E0E8;font-family:JetBrains Mono,monospace;'
                            f'font-weight:600;">{format_inr(amt)}</div>', unsafe_allow_html=True)

            sim_data.append({"name": etf, "ticker": etf_options[etf], "pct": pct, "amount": amt})
            total_pct += pct

        bcol1, bcol2 = st.columns([1, 3])
        with bcol1:
            if st.button("+ Add ETF", key="add_sim_etf"):
                st.session_state.sim_etfs = min(st.session_state.sim_etfs + 1, 8)
                st.rerun()

        # Allocation bar
        if total_pct != 100:
            st.warning(f"Total allocation: {total_pct}% — should be 100%")
        else:
            st.success(f"Total allocation: 100% of {format_inr(total_amount)}")

        if total_pct > 0 and st.button("Calculate Returns", type="primary", key="calc_multi"):
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("### Results")

            rows = []
            total_invested = 0
            total_current = 0

            # Performance chart
            fig = go.Figure()
            chart_colors = ["#5B8DEF", "#3DD598", "#FFC542", "#FC5A5A", "#AC6AFF", "#79C0FF", "#FF6B9D", "#00D4AA"]

            for idx, sd in enumerate(sim_data):
                if sd["pct"] == 0:
                    continue
                df = fetch_etf_data(sd["ticker"], period_map[sim_period])
                result = _lumpsum_return(df, sd["amount"])
                total_invested += result["invested"]
                total_current += result["current_value"]

                ret_color = "#3DD598" if result["return_pct"] >= 0 else "#FC5A5A"
                rows.append({
                    "ETF": sd["name"].split("(")[0].strip(),
                    "Invested": format_inr(sd["amount"]),
                    "Current": format_inr(result["current_value"]),
                    "P&L": format_inr(result.get("abs_return", 0)),
                    "Return %": result["return_pct"],
                })

                # Add to chart
                if not df.empty and "Close" in df.columns:
                    close = df["Close"].dropna()
                    if len(close) > 1 and float(close.iloc[0]) > 0:
                        growth = (close / close.iloc[0]) * sd["amount"]
                        fig.add_trace(go.Scatter(
                            x=close.index, y=growth,
                            name=sd["name"].split("(")[0].strip()[:18],
                            mode="lines",
                            line=dict(width=2.5, color=chart_colors[idx % len(chart_colors)]),
                            stackgroup="one",
                        ))

            # Summary cards
            total_pl = total_current - total_invested
            total_ret = ((total_current / total_invested) - 1) * 100 if total_invested > 0 else 0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Invested", format_inr(total_invested))
            m2.metric("Current Value", format_inr(total_current))
            m3.metric("Profit / Loss", format_inr(total_pl),
                       delta=f"{'+' if total_ret >= 0 else ''}{total_ret:.2f}%")
            m4.metric("Period", sim_period)

            # Chart
            if fig.data:
                fig.update_layout(
                    template="plotly_dark", height=380,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
                    yaxis_title="Value (₹)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=10, color="#8B8B9E")),
                    margin=dict(l=60, r=10, t=20, b=40),
                    xaxis=dict(gridcolor="#1E1E2D"), yaxis=dict(gridcolor="#1E1E2D"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Table
            if rows:
                rdf = pd.DataFrame(rows)
                st.dataframe(rdf, use_container_width=True, hide_index=True,
                             column_config={"Return %": st.column_config.NumberColumn(format="%+.2f%%")})

            # Pie chart
            pie_col1, pie_col2 = st.columns(2)
            with pie_col1:
                labels = [sd["name"].split("(")[0].strip()[:15] for sd in sim_data if sd["pct"] > 0]
                values = [sd["pct"] for sd in sim_data if sd["pct"] > 0]
                fig_pie = go.Figure(go.Pie(
                    labels=labels, values=values,
                    hole=0.55,
                    marker=dict(colors=chart_colors[:len(labels)]),
                    textfont=dict(size=11, color="#E0E0E8"),
                    textinfo="label+percent",
                ))
                fig_pie.update_layout(
                    template="plotly_dark", height=280,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
                    annotations=[dict(text=f"₹{total_invested/100000:.0f}L", x=0.5, y=0.5,
                                       font=dict(size=16, color="#F0F0F5", family="JetBrains Mono"),
                                       showarrow=False)],
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with pie_col2:
                st.markdown(
                    f'<div class="glass-card">'
                    f'<h3 style="margin-top:0;">Summary</h3>'
                    f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1E1E2D;">'
                    f'<span style="color:#6B6B80;">Invested</span>'
                    f'<span style="color:#F0F0F5;font-family:JetBrains Mono,monospace;">{format_inr(total_invested)}</span></div>'
                    f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1E1E2D;">'
                    f'<span style="color:#6B6B80;">Current Value</span>'
                    f'<span style="color:#F0F0F5;font-family:JetBrains Mono,monospace;">{format_inr(total_current)}</span></div>'
                    f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1E1E2D;">'
                    f'<span style="color:#6B6B80;">Profit/Loss</span>'
                    f'<span style="color:{"#3DD598" if total_pl >= 0 else "#FC5A5A"};'
                    f'font-family:JetBrains Mono,monospace;font-weight:700;">'
                    f'{"+" if total_pl >= 0 else ""}{format_inr(total_pl)}</span></div>'
                    f'<div style="display:flex;justify-content:space-between;padding:8px 0;">'
                    f'<span style="color:#6B6B80;">Total Return</span>'
                    f'<span style="color:{"#3DD598" if total_ret >= 0 else "#FC5A5A"};'
                    f'font-family:JetBrains Mono,monospace;font-weight:700;font-size:1.2rem;">'
                    f'{"+" if total_ret >= 0 else ""}{total_ret:.2f}%</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ========================
    # TAB 2: LUMPSUM CALCULATOR
    # ========================
    with tab2:
        st.markdown("### One-Time Lumpsum Return Calculator")

        lc1, lc2, lc3 = st.columns([3, 1, 1])
        with lc1:
            lump_etf = st.selectbox("Select ETF", list(etf_options.keys()), key="lump_etf")
            lump_ticker = etf_options[lump_etf]
        with lc2:
            lump_amount = st.number_input("Amount (₹)", 1000, 10000000, 100000, 5000, key="lump_amt")
        with lc3:
            lump_period = st.selectbox("Period", ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y"],
                                        index=3, key="lump_period")

        period_val = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y", "3Y": "3y", "5Y": "5y"}
        df = fetch_etf_data(lump_ticker, period_val[lump_period])
        result = _lumpsum_return(df, lump_amount)

        if result["return_pct"] != 0 or result["current_value"] != lump_amount:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Invested", format_inr(result["invested"]))
            m2.metric("Current Value", format_inr(result["current_value"]))
            m3.metric("Profit/Loss", format_inr(result["abs_return"]),
                       delta=f"{'+' if result['return_pct'] >= 0 else ''}{result['return_pct']:.2f}%")
            m4.metric("Period", lump_period)

            if result.get("buy_price"):
                st.caption(f"Buy: ₹{result['buy_price']} | Current: ₹{result['curr_price']} | Units: {result['units']}")

            # Growth chart
            if not df.empty and "Close" in df.columns:
                close = df["Close"].dropna()
                if len(close) > 1 and float(close.iloc[0]) > 0:
                    growth = (close / close.iloc[0]) * lump_amount
                    is_up = float(growth.iloc[-1]) >= lump_amount
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=close.index, y=growth, mode="lines",
                        line=dict(width=2.5, color="#3DD598" if is_up else "#FC5A5A"),
                        fill="tozeroy",
                        fillcolor="rgba(61,213,152,0.08)" if is_up else "rgba(252,90,90,0.08)",
                        name="Portfolio Value"
                    ))
                    fig.add_hline(y=lump_amount, line_dash="dash", line_color="#6B6B80",
                                  annotation_text=f"Invested: {format_inr(lump_amount)}")
                    fig.update_layout(
                        template="plotly_dark", height=350,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
                        yaxis_title="Value (₹)", margin=dict(l=60, r=10, t=20, b=40),
                        xaxis=dict(gridcolor="#1E1E2D"), yaxis=dict(gridcolor="#1E1E2D"),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for this ETF/period.")

    # ========================
    # TAB 3: SIP CALCULATOR
    # ========================
    with tab3:
        st.markdown("### Monthly SIP Return Calculator")

        sc1, sc2 = st.columns(2)
        with sc1:
            sip_etf = st.selectbox("Select ETF", list(etf_options.keys()), key="sip_etf_calc")
            sip_ticker = etf_options[sip_etf]
        with sc2:
            sip_amount = st.number_input("Monthly SIP (₹)", 500, 100000, 5000, 500, key="sip_amt_calc")

        sip_df = fetch_etf_data(sip_ticker, "5y")
        if not sip_df.empty and "Close" in sip_df.columns:
            result = sip_simulator(sip_df, sip_amount)
            profit = result["current_value"] - result["invested"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Invested", format_inr(result["invested"]))
            m2.metric("Current Value", format_inr(result["current_value"]))
            m3.metric("Profit/Loss", format_inr(profit),
                       delta=f"{'+' if result['return_pct'] >= 0 else ''}{result['return_pct']:.2f}%")
            m4.metric("Units", f"{result['units']:.2f}")

            # SIP growth chart
            monthly = sip_df["Close"].resample("ME").last().dropna()
            if len(monthly) > 2:
                invested_line = []
                value_line = []
                total_units = 0
                total_inv = 0
                for price in monthly:
                    p = float(price)
                    if p > 0:
                        total_units += sip_amount / p
                        total_inv += sip_amount
                    invested_line.append(total_inv)
                    value_line.append(total_units * p)

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=monthly.index, y=value_line, name="Portfolio Value",
                                          line=dict(color="#3DD598", width=2.5),
                                          fill="tozeroy", fillcolor="rgba(61,213,152,0.08)"))
                fig.add_trace(go.Scatter(x=monthly.index, y=invested_line, name="Amount Invested",
                                          line=dict(color="#5B8DEF", width=2, dash="dash")))
                fig.update_layout(
                    template="plotly_dark", height=350,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#13131A",
                    yaxis_title="Value (₹)", margin=dict(l=60, r=10, t=20, b=40),
                    xaxis=dict(gridcolor="#1E1E2D"), yaxis=dict(gridcolor="#1E1E2D"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for SIP simulation.")

    # ========================
    # TAB 4: MODEL PORTFOLIOS
    # ========================
    with tab4:
        st.markdown("### Pre-Built War-Era Portfolios")
        st.caption("₹5,000/month base | [FORECAST — NOT GUARANTEED]")

        st.markdown(
            '<div style="background:#FC5A5A12;border:1px solid #FC5A5A30;border-radius:12px;padding:14px 20px;margin-bottom:16px;">'
            '<span style="color:#FC5A5A;font-weight:700;">RECOMMENDED:</span> '
            '<span style="color:#E0E0E8;">Ultra War-Era Portfolio — based on 1Y returns: '
            'Silver +149% | Gold +74% | PSU Bank +49% | Defence +41%</span></div>',
            unsafe_allow_html=True
        )

        _render_portfolio_template(PORTFOLIO_ULTRA)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        _render_portfolio_template(PORTFOLIO_AGGRESSIVE)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        _render_portfolio_template(PORTFOLIO_HEDGED)
