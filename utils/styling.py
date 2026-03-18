"""Premium Trading Dashboard UI — inspired by Stockin UI Kit."""
import streamlit as st


def war_signal_color(signal: str) -> str:
    return {"GREEN": "#3DD598", "AMBER": "#FFC542", "RED": "#FC5A5A"}.get(signal, "#ffffff")


def delta_color(value: float) -> str:
    return "#3DD598" if value > 0 else ("#FC5A5A" if value < 0 else "#8B8B8B")


def format_inr(value: float) -> str:
    if value >= 10_000_000:
        return f"\u20b9{value/10_000_000:.2f} Cr"
    elif value >= 100_000:
        return f"\u20b9{value/100_000:.2f} L"
    elif value >= 1000:
        return f"\u20b9{value:,.0f}"
    return f"\u20b9{value:.2f}"


def signal_badge(signal: str) -> str:
    color = war_signal_color(signal)
    return (f'<span style="background:{color}22;color:{color};padding:4px 14px;'
            f'border-radius:6px;font-weight:600;font-size:0.85em;">{signal}</span>')


def category_badge(category: str) -> str:
    colors = {
        "Defence": "#FC5A5A", "Defence/PSU": "#FC5A5A",
        "Gold": "#FFC542", "Silver": "#B8B8D0",
        "PSU Bank": "#3DD598", "Infrastructure": "#3DD598",
        "Nifty 50": "#5B8DEF", "Nifty Next 50": "#5B8DEF",
        "Midcap": "#5B8DEF", "Midcap 150": "#5B8DEF",
        "Banking": "#5B8DEF", "IT": "#AC6AFF",
        "Pharma": "#3DD598", "US Tech": "#AC6AFF",
    }
    c = colors.get(category, "#5B8DEF")
    return (f'<span style="background:{c}18;color:{c};padding:3px 10px;'
            f'border-radius:6px;font-size:0.72em;font-weight:600;">{category}</span>')


def data_source_badge(source: str) -> str:
    """Show which data source is active."""
    icons = {"yfinance": "\u2713", "stooq": "\u26a1", "cache": "\u23f3"}
    colors = {"yfinance": "#3DD598", "stooq": "#FFC542", "cache": "#FC5A5A"}
    icon = icons.get(source, "")
    color = colors.get(source, "#6B6B80")
    return (f'<span class="data-source-badge" style="background:{color}18;color:{color};'
            f'padding:3px 10px;border-radius:6px;font-size:0.72em;font-weight:600;">'
            f'{icon} {source}</span>')


def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ====== BASE ====== */
    .stApp {
        background: #0D0D12;
        color: #E8E8ED;
        font-family: 'DM Sans', -apple-system, sans-serif;
    }
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 1440px;
    }

    /* ====== SIDEBAR ====== */
    section[data-testid="stSidebar"] {
        background: #13131A;
        border-right: 1px solid #1E1E2D;
        width: 240px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
        color: #8B8B9E;
        font-weight: 500;
        font-size: 0.9rem;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        padding: 10px 14px;
        border-radius: 8px;
        transition: all 0.2s;
        border-left: 3px solid transparent;
        margin: 2px 0;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        background: #1A1A28;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        background: #5B8DEF15 !important;
        border-left: 3px solid #5B8DEF !important;
        color: #5B8DEF !important;
    }

    /* ====== HEADER BAR ====== */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 14px;
        margin-bottom: 16px;
        border-bottom: 1px solid #1E1E2D;
    }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .header-right { display: flex; align-items: center; gap: 14px; }
    .header-search {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 10px;
        padding: 8px 16px;
        color: #6B6B80;
        font-size: 0.82rem;
        width: 260px;
        font-family: 'DM Sans', sans-serif;
    }
    .header-icon {
        width: 36px; height: 36px; border-radius: 10px;
        background: #16161F; border: 1px solid #1E1E2D;
        display: flex; align-items: center; justify-content: center;
        color: #8B8B9E; font-size: 1rem; cursor: pointer;
        transition: all 0.15s;
    }
    .header-icon:hover { background: #1A1A28; border-color: #2A2A3D; }
    .header-avatar {
        width: 36px; height: 36px; border-radius: 50%;
        background: linear-gradient(135deg, #5B8DEF, #AC6AFF);
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-weight: 700; font-size: 0.85rem;
    }

    /* ====== METRICS — PORTFOLIO CARDS ====== */
    [data-testid="stMetric"] {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 18px 22px;
        transition: all 0.25s ease;
    }
    [data-testid="stMetric"]:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #6B6B80 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        color: #F0F0F5 !important;
        font-weight: 700 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stMetricDelta"] svg { display: none; }

    /* ====== TYPOGRAPHY ====== */
    h1 {
        color: #F0F0F5 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        letter-spacing: -0.3px;
    }
    h2, .stMarkdown h2 {
        color: #E0E0E8 !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        margin-bottom: 0.8rem !important;
    }
    h3 {
        color: #C0C0CC !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    p, li, span { color: #A0A0B0; }

    /* ====== DATAFRAME / TABLE ====== */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #1E1E2D;
    }
    [data-testid="stDataFrame"] table {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
    }
    [data-testid="stDataFrame"] th {
        background: #16161F !important;
        color: #6B6B80 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.72rem !important;
        letter-spacing: 0.5px;
    }
    [data-testid="stDataFrame"] td {
        background: #0D0D12 !important;
        border-color: #1A1A28 !important;
    }
    [data-testid="stDataFrame"] tr:nth-child(even) td {
        background: #111118 !important;
    }

    /* ====== TABS ====== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #13131A;
        border-radius: 10px;
        padding: 3px;
        border: 1px solid #1E1E2D;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 500;
        color: #6B6B80;
        padding: 8px 20px;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: #5B8DEF !important;
        color: #fff !important;
        font-weight: 600;
    }

    /* ====== BUTTONS ====== */
    .stButton > button {
        background: #5B8DEF;
        border: none;
        border-radius: 8px;
        color: #fff;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #4A7DE0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(91,141,239,0.3);
    }

    /* ====== INPUTS ====== */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stNumberInput > div > div > input {
        background: #16161F !important;
        border: 1px solid #1E1E2D !important;
        border-radius: 10px !important;
        color: #E0E0E8 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within {
        border-color: #5B8DEF !important;
    }

    /* ====== ALERTS ====== */
    .stAlert { border-radius: 10px; border: none; }
    div[data-testid="stAlert"] > div { font-size: 0.88rem; }

    /* ====== CUSTOM COMPONENTS ====== */
    .signal-box {
        padding: 16px 24px;
        border-radius: 12px;
        margin: 12px 0;
        text-align: center;
        font-size: 0.95em;
        font-weight: 600;
    }
    .news-item {
        padding: 14px 18px;
        margin: 6px 0;
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 10px;
        transition: all 0.15s;
    }
    .news-item:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
    }
    .news-item-accent {
        padding: 14px 18px;
        margin: 6px 0;
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-left: 3px solid #5B8DEF;
        border-radius: 0 10px 10px 0;
        transition: all 0.15s;
    }
    .news-item-accent:hover { background: #1A1A28; border-color: #2A2A3D; border-left-color: #5B8DEF; }
    .news-item-accent.high { border-left-color: #FC5A5A; }
    .news-item-accent.medium { border-left-color: #FFC542; }
    .news-item-accent.low { border-left-color: #3DD598; }

    .glass-card {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 22px;
        margin: 10px 0;
        transition: all 0.25s;
    }
    .glass-card:hover {
        border-color: #2A2A3D;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    /* ====== PORTFOLIO CARDS v2 (Kit-matching) ====== */
    .portfolio-card-v2 {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 18px;
        position: relative;
        transition: all 0.25s;
        height: 100%;
    }
    .portfolio-card-v2:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateY(-3px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.3);
    }
    .portfolio-card-v2 .card-icon {
        width: 40px; height: 40px; border-radius: 10px;
        background: #1E1E2D;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem; margin-bottom: 10px;
    }
    .portfolio-card-v2 .delta-badge {
        position: absolute; top: 14px; right: 14px;
        padding: 3px 10px; border-radius: 6px;
        font-size: 0.78rem; font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .portfolio-card-v2 .meta-row {
        display: flex; justify-content: space-between;
        margin-top: 8px; gap: 12px;
    }
    .portfolio-card-v2 .meta-label {
        color: #6B6B80; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .portfolio-card-v2 .meta-value {
        color: #F0F0F5;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700; font-size: 0.92rem;
    }

    /* ====== STAT CARD (Views All style) ====== */
    .stat-card {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 18px 22px;
        transition: all 0.25s;
    }
    .stat-card:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    .stat-card .label {
        color: #6B6B80; font-size: 0.75rem;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .stat-card .value {
        color: #F0F0F5; font-family: 'JetBrains Mono', monospace;
        font-weight: 700; font-size: 1.2rem; margin: 6px 0;
    }
    .stat-card .trend {
        display: inline-flex; align-items: center;
        gap: 4px; font-size: 0.75rem;
        padding: 2px 8px; border-radius: 4px;
        font-family: 'JetBrains Mono', monospace; font-weight: 600;
    }
    .stat-card .trend.up { background: #3DD59818; color: #3DD598; }
    .stat-card .trend.down { background: #FC5A5A18; color: #FC5A5A; }

    /* ====== COLORED SUMMARY CARDS (Wallet) ====== */
    .summary-card {
        border-radius: 14px; padding: 20px 24px;
        transition: all 0.25s;
    }
    .summary-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }
    .summary-card .sc-label { color: rgba(255,255,255,0.6); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .summary-card .sc-value { color: #fff; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 1.3rem; margin-top: 6px; }
    .summary-card.blue { background: linear-gradient(135deg, #1a2a6c, #2a4a9c); border: 1px solid #3a5aac; }
    .summary-card.green { background: linear-gradient(135deg, #1a4a2c, #2a6a3c); border: 1px solid #3a7a4c; }
    .summary-card.yellow { background: linear-gradient(135deg, #4a3a1a, #6a5a2a); border: 1px solid #7a6a3a; }
    .summary-card.red { background: linear-gradient(135deg, #4a1a1a, #6a2a2a); border: 1px solid #7a3a3a; }

    /* ====== MARKET TABLE ROW v2 ====== */
    .market-row {
        display: flex;
        align-items: center;
        padding: 12px 18px;
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 10px;
        margin: 4px 0;
        transition: all 0.2s;
    }
    .market-row:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateX(2px);
    }
    .market-row .etf-icon {
        width: 32px; height: 32px; border-radius: 8px;
        background: #1E1E2D; margin-right: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; color: #8B8B9E; flex-shrink: 0;
    }
    .market-row .etf-info { flex: 2; }
    .market-row .etf-name {
        color: #E0E0E8; font-weight: 600; font-size: 0.88rem;
    }
    .market-row .etf-cat {
        color: #6B6B80; font-size: 0.7rem;
    }
    .market-row .etf-price {
        flex: 1; color: #F0F0F5;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500; font-size: 0.85rem; text-align: right;
    }
    .market-row .etf-change {
        flex: 1; font-family: 'JetBrains Mono', monospace;
        font-weight: 600; font-size: 0.85rem; text-align: right;
    }
    .market-row .etf-spark {
        flex: 1; text-align: right; padding-left: 8px;
    }
    .market-row .etf-score {
        flex: 0.8; font-family: 'JetBrains Mono', monospace;
        font-weight: 600; font-size: 0.7rem; text-align: right;
        color: #FFC542;
    }

    /* ====== PILL FILTERS ====== */
    .pill-container {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin: 12px 0;
    }
    .pill {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #1E1E2D;
        color: #8B8B9E;
        background: #16161F;
    }
    .pill:hover { background: #1A1A28; border-color: #2A2A3D; }
    .pill-active {
        background: #5B8DEF;
        color: #fff;
        border-color: #5B8DEF;
        box-shadow: 0 2px 8px rgba(91,141,239,0.3);
    }

    /* ====== SECTION DIVIDER ====== */
    .section-divider {
        border: none;
        height: 1px;
        background: #1E1E2D;
        margin: 20px 0;
    }

    /* ====== SECTION HEADER with "See All" ====== */
    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 12px;
    }
    .section-header h3 { margin: 0 !important; }
    .section-header .see-all {
        color: #5B8DEF; font-size: 0.82rem; font-weight: 600;
        cursor: pointer; text-decoration: none;
    }
    .section-header .see-all:hover { text-decoration: underline; }

    /* ====== WAR TILT CARDS ====== */
    .tilt-card {
        background: #16161F; border: 1px solid #1E1E2D;
        border-radius: 12px; padding: 16px;
        transition: all 0.2s;
    }
    .tilt-card:hover { background: #1A1A28; border-color: #2A2A3D; }
    .tilt-card.beneficiary { border-left: 3px solid #3DD598; }
    .tilt-card.victim { border-left: 3px solid #FC5A5A; }
    .tilt-card.neutral { border-left: 3px solid #5B8DEF; }

    /* ====== DATA SOURCE BADGE ====== */
    .data-source-badge {
        font-family: 'JetBrains Mono', monospace;
    }

    /* ====== FALLBACK CARD ====== */
    .fallback-card {
        background: #16161F; border: 1px solid #FFC54230;
        border-radius: 12px; padding: 18px 22px;
        display: flex; align-items: center; gap: 14px;
    }
    .fallback-card .fb-icon { font-size: 1.5rem; }
    .fallback-card .fb-text { color: #A0A0B0; font-size: 0.88rem; }
    .fallback-card .fb-price { color: #FFC542; font-family: 'JetBrains Mono', monospace; font-weight: 700; }

    /* ====== PLOTLY ====== */
    .js-plotly-plot { border-radius: 12px; overflow: hidden; }

    /* ====== SCROLLBAR ====== */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2A2A3D; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #3A3A4D; }

    /* ====== EXPANDER ====== */
    .streamlit-expanderHeader {
        background: #16161F !important;
        border-radius: 10px !important;
        border: 1px solid #1E1E2D !important;
        font-weight: 600;
    }

    /* ====== FAVORITES LIST ====== */
    .fav-item {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #1E1E2D;
        transition: all 0.15s;
    }
    .fav-item:hover { background: #16161F; margin: 0 -8px; padding: 10px 8px; border-radius: 8px; }
    .fav-item .fav-left { display: flex; align-items: center; gap: 10px; }
    .fav-item .fav-icon {
        width: 32px; height: 32px; border-radius: 8px;
        background: #1E1E2D; display: flex; align-items: center;
        justify-content: center; font-size: 0.7rem; color: #8B8B9E;
    }
    .fav-item .fav-name { color: #E0E0E8; font-weight: 600; font-size: 0.85rem; }
    .fav-item .fav-cat { color: #6B6B80; font-size: 0.7rem; }
    .fav-item .fav-price {
        color: #F0F0F5; font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem; font-weight: 600; text-align: right;
    }
    .fav-item .fav-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem; text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)
