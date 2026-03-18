# War-Era ETF Intelligence Dashboard

A free, real-time intelligence platform for Indian retail investors operating in a multi-conflict global environment. Built with Python + Streamlit — **zero API costs**.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red) ![License](https://img.shields.io/badge/License-MIT-green) ![ETFs](https://img.shields.io/badge/ETFs_Tracked-21-gold)

## What This Does

Tracks **21 NSE/BSE-listed ETFs** through a war-economy lens — Defence, Gold, Silver, PSU, Infra, Midcap, and International — with live prices, geopolitical news, sector rotation heatmaps, and automated dip alerts.

Every analysis runs through 6 active conflict scenarios: Russia-Ukraine, Israel-Iran, China-Taiwan, US trade wars, India-Pakistan, and global stagflation.

## Dashboard Modules

| Module | What It Shows |
|--------|---------------|
| **Command Center** | Portfolio cards, top gainers/losers, performance chart, war signal (GREEN/AMBER/RED), conflict news feed, AI insight |
| **Market Pulse** | All 21 ETFs with live prices, 1D change, war scores, volume spike alerts, mini sparkline charts |
| **ETF Comparison** | Normalized performance charts, return tables (1D to 5Y), drawdown analysis, SIP simulator |
| **Sector Rotation** | NSE sector heatmap with 5D/30D momentum, war-beneficiary vs war-victim classification |
| **Macro Signals** | Gold, Silver, USD/INR, Brent Crude, US 10Y Yield, India VIX — with sparklines and threshold alerts |
| **Portfolio Tracker** | Multi-ETF investment simulator, lumpsum calculator, SIP calculator, 3 model portfolios |
| **Geopolitical Tracker** | Live conflict news, intensity score, 6-scenario impact map with investor actions |

## ETFs Tracked (All Verified on Yahoo Finance)

**Defence:** MODEFENCE, GROWWDEFNC, CPSEETF
**Gold:** GOLDBEES, SETFGOLD, HDFCGOLD, GOLD1
**Silver:** SILVERBEES, HDFCSILVER
**PSU/Infra:** PSUBNKBEES, INFRABEES
**Core India:** NIFTYBEES, JUNIORBEES, MOM100, MIDCAPETF
**Sectoral:** BANKBEES, ITBEES, PHARMABEES
**International:** MON100, MONQ50

## Model Portfolios (₹5,000/month SIP)

**Ultra War-Era (Recommended):**
| ETF | Allocation | 1Y Return |
|-----|-----------|-----------|
| Silver (SILVERBEES) | 40% | +149% |
| Defence (MODEFENCE) | 30% | +41% |
| Gold (GOLDBEES) | 20% | +74% |
| PSU Bank (PSUBNKBEES) | 10% | +49% |

Also includes: Maximum Aggression and Geopolitical Hedge variants.

## Price Alert System

Background service that monitors Gold & Silver prices every 15 minutes and sends alerts on:
- RSI oversold (< 35) — BUY signal
- Corrections > 7-10% from recent high
- Key support level breaks
- Bounce detection (dip ending)
- Daily summary with signal (BUY/HOLD/WAIT)

**Notification channels:**
- Windows Toast notifications (runs via Task Scheduler)
- Telegram Bot (free, works when PC is off)
- Make.com webhook (optional)
- Local alert log file

## Quick Start

```bash
# Clone
git clone https://github.com/theyashsisodiya/stock-market-free-analysis.git
cd stock-market-free-analysis

# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run app.py

# Setup price alerts (optional)
python setup_alerts.py
```

## Requirements

- Python 3.10+
- No API keys needed — all data from free public sources

## Data Sources (All Free)

| Data | Source |
|------|--------|
| ETF/Stock prices | Yahoo Finance (via yfinance) |
| Conflict news | Google News RSS |
| Geopolitical events | GDELT Project |
| NSE Sector indices | Yahoo Finance |
| Macro (Gold, Crude, VIX) | Yahoo Finance |

## Tech Stack

- **Frontend:** Streamlit with custom dark UI (DM Sans + JetBrains Mono)
- **Data:** yfinance, feedparser, requests
- **Charts:** Plotly with dark theme
- **Alerts:** plyer (Windows toast), Telegram Bot API, Make.com webhooks
- **Scheduling:** Windows Task Scheduler

## Project Structure

```
quant-project/
├── app.py                    # Main Streamlit app
├── config.py                 # ETF universe, scenarios, portfolios
├── cloud_alert.py            # Price alert service
├── price_alert.py            # Local notification service
├── setup_alerts.py           # Alert setup wizard
├── requirements.txt
├── data/
│   └── fetchers.py           # All API calls (cached with st.cache_data)
├── modules/
│   ├── intelligence_feed.py  # Command Center (home page)
│   ├── market_pulse.py       # Live market data
│   ├── etf_comparison.py     # Compare & simulate
│   ├── sector_rotation.py    # Sector heatmap
│   ├── macro_signals.py      # Macro indicators
│   ├── portfolio_tracker.py  # Portfolio & calculators
│   └── geopolitical_tracker.py
└── utils/
    └── styling.py            # Premium dark UI theme
```

## Disclaimer

This is **not financial advice**. All forecasts are estimates. Past performance does not guarantee future returns. Built for educational and research purposes.

## License

MIT

---

Built for Indian retail investors navigating a multi-conflict world.
