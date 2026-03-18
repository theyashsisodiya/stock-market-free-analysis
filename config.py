"""Configuration — War-Era ETF Intelligence Dashboard"""

# --- ETF Universe (ALL verified on Yahoo Finance — Mar 2026) ---
WAR_ECONOMY_ETFS = {
    # Defence (War-Core)
    "MODEFENCE.NS":   {"name": "Motilal Oswal Defence ETF", "category": "Defence", "war_score": 10},
    "GROWWDEFNC.NS":  {"name": "Groww Nifty India Defence ETF", "category": "Defence", "war_score": 10},
    "CPSEETF.NS":     {"name": "CPSE ETF (Defence+Energy PSU)", "category": "Defence/PSU", "war_score": 9},
    # Gold (Safe Haven)
    "GOLDBEES.NS":    {"name": "Nippon Gold BeES", "category": "Gold", "war_score": 9},
    "SETFGOLD.NS":    {"name": "SBI Gold ETF", "category": "Gold", "war_score": 9},
    "HDFCGOLD.NS":    {"name": "HDFC Gold ETF", "category": "Gold", "war_score": 9},
    "GOLD1.NS":       {"name": "ICICI Prudential Gold ETF", "category": "Gold", "war_score": 8},
    # Silver (Industrial + Monetary — #1 performer +149% 1Y)
    "SILVERBEES.NS":  {"name": "Nippon India Silver ETF", "category": "Silver", "war_score": 10},
    "HDFCSILVER.NS":  {"name": "HDFC Silver ETF", "category": "Silver", "war_score": 9},
    # PSU / Infra
    "PSUBNKBEES.NS":  {"name": "Nippon PSU Bank BeES", "category": "PSU Bank", "war_score": 7},
    "INFRABEES.NS":   {"name": "Nippon Infra BeES", "category": "Infrastructure", "war_score": 7},
    # Core India
    "NIFTYBEES.NS":   {"name": "Nippon Nifty 50 BeES", "category": "Nifty 50", "war_score": 5},
    "JUNIORBEES.NS":  {"name": "Nippon Junior BeES (Next 50)", "category": "Nifty Next 50", "war_score": 5},
    "MOM100.NS":      {"name": "Motilal Oswal Midcap 100 ETF", "category": "Midcap", "war_score": 5},
    "MIDCAPETF.NS":   {"name": "Nippon Midcap 150 ETF", "category": "Midcap 150", "war_score": 5},
    # Sectoral
    "BANKBEES.NS":    {"name": "Nippon Bank BeES", "category": "Banking", "war_score": 4},
    "ITBEES.NS":      {"name": "Nippon IT BeES", "category": "IT", "war_score": 3},
    "PHARMABEES.NS":  {"name": "Nippon Pharma BeES", "category": "Pharma", "war_score": 4},
    # International
    "MON100.NS":      {"name": "Motilal Oswal Nasdaq 100 ETF", "category": "US Tech", "war_score": 4},
    "MONQ50.NS":      {"name": "Motilal Oswal Nasdaq Q50 ETF", "category": "US Tech", "war_score": 4},
}

# --- Default comparison set (top performers) ---
DEFAULT_COMPARISON = [
    "SILVERBEES.NS", "GOLDBEES.NS", "MODEFENCE.NS",
    "GROWWDEFNC.NS", "PSUBNKBEES.NS"
]

# --- Conflict Regions for GDELT ---
CONFLICT_REGIONS = [
    "Russia", "Ukraine", "Israel", "Iran", "Gaza", "Hezbollah",
    "Taiwan", "China", "Pakistan", "Afghanistan", "India defence",
    "Strait of Hormuz", "NATO", "Yemen", "Houthi"
]

# --- NSE Sectoral Indices ---
SECTORS = {
    "NIFTY IT":       {"war_tilt": "victim",      "ticker": "^CNXIT"},
    "NIFTY METAL":    {"war_tilt": "beneficiary",  "ticker": "^CNXMETAL"},
    "NIFTY ENERGY":   {"war_tilt": "beneficiary",  "ticker": "^CNXENERGY"},
    "NIFTY PHARMA":   {"war_tilt": "neutral",      "ticker": "^CNXPHARMA"},
    "NIFTY FMCG":     {"war_tilt": "neutral",      "ticker": "^CNXFMCG"},
    "NIFTY PSU BANK": {"war_tilt": "beneficiary",  "ticker": "^CNXPSUBANK"},
    "NIFTY INFRA":    {"war_tilt": "beneficiary",  "ticker": "^CNXINFRA"},
    "NIFTY BANK":     {"war_tilt": "neutral",      "ticker": "^NSEBANK"},
}

# --- Macro Tickers ---
MACRO = {
    "gold_usd":    "GC=F",
    "silver_usd":  "SI=F",
    "usd_inr":     "USDINR=X",
    "us_10y":      "^TNX",
    "brent_crude":  "BZ=F",
    "india_vix":   "^INDIAVIX",
    "nifty50":     "^NSEI",
}

# --- Thresholds ---
ALERTS = {
    "gold_usd_high": 3000,
    "india_vix_high": 20,
    "crude_high": 90,
    "usd_inr_high": 87,
}

# --- Conflict Scenarios ---
SCENARIOS = [
    {"scenario": "China invades Taiwan", "winner": "Defence, Gold, Silver, India Manufacturing",
     "loser": "US Tech, Semiconductors, Nasdaq FoFs", "probability": "15-20%",
     "timeline": "2025-2028", "action": "Rotate 30% from Nasdaq FoF to Defence + Gold"},
    {"scenario": "Iran closes Strait of Hormuz", "winner": "Gold, Silver, Energy PSUs, Defence",
     "loser": "FMCG, IT (INR depreciation offset)", "probability": "20-25%",
     "timeline": "2025-2026", "action": "Add Gold + Silver ETFs, hold Defence"},
    {"scenario": "Russia-Ukraine ceasefire", "winner": "European equities, IT (risk-on), FMCG",
     "loser": "Gold (short-term dip), Defence (profit booking)", "probability": "25-30%",
     "timeline": "2025-2026", "action": "Hold Defence (India cycle independent), trim Gold 10%"},
    {"scenario": "US-China trade war escalates", "winner": "India Manufacturing, Infra, PSU, Defence",
     "loser": "Nasdaq FoFs, IT services", "probability": "60-70%",
     "timeline": "2025-2027", "action": "Add Infra + Midcap India ETFs"},
    {"scenario": "India-Pakistan border flare-up", "winner": "Defence (HAL, BEL, BDL), Gold",
     "loser": "Nifty50 (short-term), Realty, FMCG", "probability": "15-20%",
     "timeline": "Any time", "action": "Hold Defence, add Gold on dip, hold Nifty SIP"},
    {"scenario": "Global stagflation from war", "winner": "Gold, Silver, Commodities, Energy",
     "loser": "Growth stocks, IT, Realty, FMCG", "probability": "30-40%",
     "timeline": "2025-2028", "action": "Max tilt Gold + Silver, reduce Nasdaq FoF to zero"},
]

# --- SIP Portfolio Templates ---
PORTFOLIO_AGGRESSIVE = {
    "name": "Version A — Maximum Aggression",
    "allocations": {
        "MODEFENCE.NS":   {"pct": 30, "amt": 1500, "reason": "Defence supercycle — India order books at ATH"},
        "GOLDBEES.NS":    {"pct": 25, "amt": 1250, "reason": "Structural gold bull — war floor + INR hedge"},
        "SILVERBEES.NS":  {"pct": 15, "amt": 750, "reason": "Industrial + monetary metal — solar + EV demand"},
        "MOM100.NS":      {"pct": 20, "amt": 1000, "reason": "India midcap growth — China+1 beneficiary"},
        "MON100.NS":      {"pct": 10, "amt": 500, "reason": "AI infrastructure demand — conflict-resistant layer"},
    },
    "expected_cagr": "18-28%",
    "max_drawdown": "-25% (Taiwan scenario)",
    "rebalance_trigger": "Defence > 40% of portfolio OR Gold breaks below $2,200"
}

PORTFOLIO_ULTRA = {
    "name": "Version B — ULTRA WAR-ERA (Safe + Ultra + Fast)",
    "base_amount": 1000000,
    "allocations": {
        "SILVERBEES.NS":  {"pct": 40, "amt": 2000, "reason": "+149% 1Y return — highest-conviction bet; fastest mover in war scenarios (Hormuz, Ukraine, stagflation). Expect 30-50%+ on any escalation."},
        "MODEFENCE.NS":   {"pct": 30, "amt": 1500, "reason": "+41% 1Y — Direct India defence orders (HAL/BEL/BDL) + border/China+1 play. Fast results from news flow."},
        "GOLDBEES.NS":    {"pct": 20, "amt": 1000, "reason": "+74% 1Y — 'Very safe' anchor — lowest volatility among winners, protects capital in global shocks."},
        "PSUBNKBEES.NS":  {"pct": 10, "amt": 500, "reason": "+49% 1Y — PSU bank re-rating play + govt capex beneficiary. Undervalued vs private banks."},
    },
    "expected_cagr": "35-55%",
    "max_drawdown": "-30% (global risk-off, but rebounds fast)",
    "rebalance_trigger": "Silver > 50% weight OR Defence ETF order book news drops"
}

PORTFOLIO_HEDGED = {
    "name": "Version B — Geopolitical Hedge",
    "allocations": {
        "GOLDBEES.NS":    {"pct": 30, "amt": 1500, "reason": "Core hedge — wins in every conflict scenario"},
        "MODEFENCE.NS":   {"pct": 25, "amt": 1250, "reason": "Defence trend — not a trade, a structural shift"},
        "NIFTYBEES.NS":   {"pct": 20, "amt": 1000, "reason": "India backbone — SIP through volatility"},
        "SILVERBEES.NS":  {"pct": 15, "amt": 750, "reason": "Precious metal diversifier + industrial upside"},
        "INFRABEES.NS":   {"pct": 10, "amt": 500, "reason": "India infra capex cycle — government push"},
    },
    "expected_cagr": "14-22%",
    "max_drawdown": "-18% (global risk-off)",
    "rebalance_trigger": "VIX > 25 sustained 5 days OR crude > $95"
}
