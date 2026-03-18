"""Premium Trading Dashboard UI — inspired by Stockin UI Kit."""
import streamlit as st


def war_signal_color(signal: str) -> str:
    return {"GREEN": "#3DD598", "AMBER": "#FFC542", "RED": "#FC5A5A"}.get(signal, "#ffffff")


def delta_color(value: float) -> str:
    return "#3DD598" if value > 0 else ("#FC5A5A" if value < 0 else "#8B8B8B")


def format_inr(value: float) -> str:
    if value >= 10_000_000:
        return f"₹{value/10_000_000:.2f} Cr"
    elif value >= 100_000:
        return f"₹{value/100_000:.2f} L"
    elif value >= 1000:
        return f"₹{value:,.0f}"
    return f"₹{value:.2f}"


def signal_badge(signal: str) -> str:
    color = war_signal_color(signal)
    return f'<span style="background:{color}22;color:{color};padding:4px 14px;border-radius:6px;font-weight:600;font-size:0.85em;">{signal}</span>'


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
    return f'<span style="background:{c}18;color:{c};padding:3px 10px;border-radius:6px;font-size:0.72em;font-weight:600;">{category}</span>'


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
        padding: 1.2rem 2rem;
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
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.15s;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        background: #1A1A28;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        background: #1F1F32 !important;
        color: #fff !important;
    }

    /* ====== METRICS — PORTFOLIO CARDS ====== */
    [data-testid="stMetric"] {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 18px 22px;
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateY(-1px);
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
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background: #4A7DE0;
        transform: translateY(-1px);
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
    .glass-card {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 22px;
        margin: 10px 0;
    }
    .glass-card:hover {
        border-color: #2A2A3D;
    }

    /* ====== PORTFOLIO CARDS ROW ====== */
    .portfolio-card {
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 14px;
        padding: 18px;
        transition: all 0.2s;
        height: 100%;
    }
    .portfolio-card:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
        transform: translateY(-2px);
    }
    .portfolio-card .name {
        color: #E0E0E8;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .portfolio-card .category {
        color: #6B6B80;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .portfolio-card .price {
        color: #F0F0F5;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.15rem;
        margin: 8px 0 2px;
    }
    .portfolio-card .change {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .change-up { color: #3DD598; }
    .change-down { color: #FC5A5A; }

    /* ====== MARKET TABLE ROW ====== */
    .market-row {
        display: flex;
        align-items: center;
        padding: 12px 18px;
        background: #16161F;
        border: 1px solid #1E1E2D;
        border-radius: 10px;
        margin: 4px 0;
        transition: all 0.15s;
    }
    .market-row:hover {
        background: #1A1A28;
        border-color: #2A2A3D;
    }
    .market-row .etf-name {
        flex: 2;
        color: #E0E0E8;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .market-row .etf-price {
        flex: 1;
        color: #F0F0F5;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        font-size: 0.85rem;
        text-align: right;
    }
    .market-row .etf-change {
        flex: 1;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: right;
    }
    .market-row .etf-return {
        flex: 1;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: right;
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
        transition: all 0.15s;
        border: 1px solid #1E1E2D;
        color: #8B8B9E;
        background: #16161F;
    }
    .pill-active {
        background: #5B8DEF;
        color: #fff;
        border-color: #5B8DEF;
    }

    /* ====== SECTION DIVIDER ====== */
    .section-divider {
        border: none;
        height: 1px;
        background: #1E1E2D;
        margin: 20px 0;
    }

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
    </style>
    """, unsafe_allow_html=True)
