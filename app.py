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
    page_icon="\U0001f3af",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

# === SIDEBAR ===
with st.sidebar:
    st.markdown(
        '<div style="padding:18px 0 10px;text-align:center;">'
        '<div style="width:42px;height:42px;border-radius:12px;'
        'background:linear-gradient(135deg,#5B8DEF,#AC6AFF);'
        'display:inline-flex;align-items:center;justify-content:center;'
        'font-size:1.3em;margin-bottom:6px;">\U0001f3af</div><br>'
        '<span style="color:#F0F0F5;font-weight:700;font-size:1.05rem;">War-Era ETF Intel</span><br>'
        '<span style="color:#6B6B80;font-size:0.7rem;">TRADING DASHBOARD</span>'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    page = st.radio(
        "nav", [
            "\U0001f3e0  Dashboard",
            "\U0001f4ca  Stock",
            "\U0001f4c8  Compare",
            "\U0001f504  Sectors",
            "\U0001f4b9  Macro",
            "\U0001f4bc  Wallet",
            "\U0001f30d  Geopolitics",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#6B6B80;font-size:0.7rem;text-transform:uppercase;'
        'letter-spacing:1px;padding:0 12px 6px;font-weight:600;">Account</div>',
        unsafe_allow_html=True
    )

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
        '<div style="color:#4A4A5A;font-size:0.7rem;line-height:1.8;">'
        'Data: Yahoo Finance + Stooq<br>Exchange: NSE/BSE<br>21 ETFs Tracked<br><br>'
        '<em style="color:#3A3A4A;">Not financial advice.</em></div>',
        unsafe_allow_html=True
    )

# === RENDER ===
module_map = {
    "\U0001f3e0  Dashboard": "intelligence_feed",
    "\U0001f4ca  Stock": "market_pulse",
    "\U0001f4c8  Compare": "etf_comparison",
    "\U0001f504  Sectors": "sector_rotation",
    "\U0001f4b9  Macro": "macro_signals",
    "\U0001f4bc  Wallet": "portfolio_tracker",
    "\U0001f30d  Geopolitics": "geopolitical_tracker",
}

mod = __import__(f"modules.{module_map[page]}", fromlist=["render"])
mod.render()
