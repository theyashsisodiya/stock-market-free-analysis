"""
WAR-ERA ETF INTELLIGENCE DASHBOARD v3.0
Run: streamlit run app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.styling import apply_theme

st.set_page_config(
    page_title="War-Era ETF Intel",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# === SIDEBAR ===
with st.sidebar:
    st.markdown(
        '<div style="padding:16px 0 8px;text-align:center;">'
        '<span style="font-size:1.6em;">🎯</span><br>'
        '<span style="color:#F0F0F5;font-weight:700;font-size:1.05rem;">War-Era ETF Intel</span>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    page = st.radio(
        "nav", [
            "🏠  Dashboard",
            "📊  Stock",
            "📈  Compare",
            "🔄  Sectors",
            "💹  Macro",
            "💼  Wallet",
            "🌍  Geopolitics",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    data_mode = st.radio("Data", ["Live", "Historical"], horizontal=True, label_visibility="collapsed")
    st.session_state["data_mode"] = "Live (Today)" if data_mode == "Live" else "Historical (5Y)"

    if data_mode == "Historical":
        hp = st.select_slider("Period", ["1mo","3mo","6mo","1y","2y","5y"], value="1y",
                               format_func=lambda x: {"1mo":"1M","3mo":"3M","6mo":"6M","1y":"1Y","2y":"2Y","5y":"5Y"}[x])
        st.session_state["hist_period"] = hp
    else:
        st.session_state["hist_period"] = "1y"
        st_autorefresh(interval=60_000, limit=None, key="refresh")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#4A4A5A;font-size:0.72rem;line-height:1.7;">'
        'Data: Yahoo Finance<br>Exchange: NSE/BSE<br>21 ETFs Tracked<br><br>'
        '<em>Not financial advice.</em></div>',
        unsafe_allow_html=True
    )

# === RENDER ===
module_map = {
    "🏠  Dashboard": "intelligence_feed",
    "📊  Stock": "market_pulse",
    "📈  Compare": "etf_comparison",
    "🔄  Sectors": "sector_rotation",
    "💹  Macro": "macro_signals",
    "💼  Wallet": "portfolio_tracker",
    "🌍  Geopolitics": "geopolitical_tracker",
}

mod = __import__(f"modules.{module_map[page]}", fromlist=["render"])
mod.render()
