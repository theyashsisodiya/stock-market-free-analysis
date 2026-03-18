"""Data fetching layer — all external API calls centralized here."""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import feedparser
import streamlit as st
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


@st.cache_data(ttl=300, show_spinner=False)
def fetch_etf_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch OHLCV data for a single ETF."""
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Drop duplicate column names (e.g. 'Adj Close' and 'Close')
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception as e:
        st.toast(f"Data fetch failed for {ticker}: {e}", icon="⚠️")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner="Fetching prices...")
def fetch_batch_prices(tickers: tuple) -> dict:
    """Single yfinance call for all tickers — 1 HTTP request instead of N."""
    results = {}
    try:
        df = yf.download(list(tickers), period="5d", progress=False,
                         auto_adjust=True, group_by="ticker", threads=True)
        if df.empty:
            return {t: {"price": 0, "change_pct": 0, "prev_close": 0} for t in tickers}
        for t in tickers:
            try:
                if len(tickers) == 1:
                    ticker_df = df
                    if isinstance(ticker_df.columns, pd.MultiIndex):
                        ticker_df.columns = ticker_df.columns.get_level_values(0)
                else:
                    ticker_df = df[t]
                ticker_df = ticker_df.dropna(subset=["Close"])
                if len(ticker_df) < 1:
                    results[t] = {"price": 0, "change_pct": 0, "prev_close": 0}
                    continue
                close_today = float(ticker_df["Close"].iloc[-1])
                close_prev = float(ticker_df["Close"].iloc[-2]) if len(ticker_df) > 1 else close_today
                change_pct = ((close_today - close_prev) / close_prev) * 100 if close_prev else 0
                results[t] = {
                    "price": round(close_today, 2),
                    "change_pct": round(change_pct, 2),
                    "prev_close": round(close_prev, 2),
                }
            except Exception:
                results[t] = {"price": 0, "change_pct": 0, "prev_close": 0}
    except Exception:
        for t in tickers:
            results[t] = {"price": 0, "change_pct": 0, "prev_close": 0}
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_price(ticker: str) -> dict:
    """Get current price and change for a single ticker (uses batch internally)."""
    result = fetch_batch_prices((ticker,))
    return result.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})


@st.cache_data(ttl=300, show_spinner=False)
def fetch_volume_signal(ticker: str) -> dict:
    """Check if current volume > 2x 20-day average (war signal)."""
    try:
        df = fetch_etf_data(ticker, period="2mo")
        if df.empty or len(df) < 20 or "Volume" not in df.columns:
            return {"spike": False, "ratio": 0}
        avg_vol = df["Volume"].iloc[-21:-1].mean()
        curr_vol = df["Volume"].iloc[-1]
        ratio = float(curr_vol / avg_vol) if avg_vol > 0 else 0
        return {"spike": ratio > 2, "ratio": round(ratio, 2)}
    except Exception:
        return {"spike": False, "ratio": 0}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_macro_data() -> dict:
    """Fetch all macro indicators via batch."""
    from config import MACRO
    tickers = tuple(MACRO.values())
    batch = fetch_batch_prices(tickers)
    results = {}
    for key, ticker in MACRO.items():
        results[key] = batch.get(ticker, {"price": 0, "change_pct": 0, "prev_close": 0})
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_sector_momentum(ticker: str, days: int = 30) -> dict:
    """Calculate sector momentum scores."""
    try:
        df = fetch_etf_data(ticker, period="3mo")
        if df.empty or "Close" not in df.columns or len(df) < 6:
            return {"momentum_5d": 0, "momentum_30d": 0}
        close = df["Close"]
        m5 = float(((close.iloc[-1] / close.iloc[-6]) - 1) * 100)
        if len(close) > days:
            m30 = float(((close.iloc[-1] / close.iloc[-(days+1)]) - 1) * 100)
        else:
            m30 = float(((close.iloc[-1] / close.iloc[0]) - 1) * 100)
        return {"momentum_5d": round(m5, 2), "momentum_30d": round(m30, 2)}
    except Exception:
        return {"momentum_5d": 0, "momentum_30d": 0}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_conflict_news() -> list:
    """Fetch conflict-related news from Google News RSS (free, no API key)."""
    keywords = ["war military conflict", "defence India order",
                "Israel Iran escalation", "Russia Ukraine war",
                "gold price surge"]
    articles = []

    def _fetch_one(kw):
        try:
            url = f"https://news.google.com/rss/search?q={kw.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(url)
            items = []
            for entry in feed.entries[:3]:
                items.append({
                    "title": entry.get("title", ""),
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "published": entry.get("published", ""),
                    "link": entry.get("link", ""),
                    "keyword": kw.split()[0],
                })
            return items
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_fetch_one, kw) for kw in keywords]
        for f in as_completed(futures):
            articles.extend(f.result())

    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:20]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_gdelt_events(region: str = "India") -> list:
    """Fetch recent conflict events from GDELT."""
    try:
        url = (
            f"https://api.gdeltproject.org/api/v2/doc/doc?query={region}%20conflict"
            f"&mode=ArtList&maxrecords=10&format=json"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("articles", [])[:10]
    except Exception:
        pass
    return []


def calculate_returns(df: pd.DataFrame) -> dict:
    """Calculate return metrics from price DataFrame."""
    if df.empty or "Close" not in df.columns or len(df) < 2:
        return {"1d": 0, "1w": 0, "1m": 0, "6m": 0, "1y": 0, "cagr_3y": 0}
    close = df["Close"].dropna()
    if len(close) < 2:
        return {"1d": 0, "1w": 0, "1m": 0, "6m": 0, "1y": 0, "cagr_3y": 0}
    last = float(close.iloc[-1])
    if last == 0:
        return {"1d": 0, "1w": 0, "1m": 0, "6m": 0, "1y": 0, "cagr_3y": 0}
    returns = {}
    periods = {"1d": 1, "1w": 5, "1m": 21, "6m": 126, "1y": 252}
    for label, days in periods.items():
        if len(close) > days:
            prev = float(close.iloc[-(days+1)])
            returns[label] = round(((last / prev) - 1) * 100, 2) if prev else 0
        else:
            returns[label] = 0
    if len(close) > 252 * 3:
        prev_3y = float(close.iloc[-(252*3+1)])
        returns["cagr_3y"] = round(((last / prev_3y) ** (1/3) - 1) * 100, 2) if prev_3y else 0
    else:
        years = len(close) / 252
        first = float(close.iloc[0])
        if years > 0 and first > 0:
            returns["cagr_3y"] = round(((last / first) ** (1/years) - 1) * 100, 2)
        else:
            returns["cagr_3y"] = 0
    return returns


def calculate_max_drawdown(df: pd.DataFrame) -> float:
    """Calculate maximum drawdown percentage."""
    if df.empty or "Close" not in df.columns:
        return 0
    close = df["Close"].dropna()
    if len(close) < 2:
        return 0
    peak = close.expanding(min_periods=1).max()
    drawdown = (close - peak) / peak
    return round(float(drawdown.min()) * 100, 2)


def sip_simulator(df: pd.DataFrame, monthly_amount: float) -> dict:
    """Simulate SIP returns on historical data."""
    if df.empty or "Close" not in df.columns or len(df) < 30:
        return {"units": 0, "invested": 0, "current_value": 0, "return_pct": 0}
    monthly = df["Close"].resample("ME").last().dropna()
    if len(monthly) < 2:
        return {"units": 0, "invested": 0, "current_value": 0, "return_pct": 0}
    total_units = 0
    total_invested = 0
    for price in monthly.iloc[:-1]:
        p = float(price)
        if p > 0:
            total_units += monthly_amount / p
            total_invested += monthly_amount
    current_value = total_units * float(monthly.iloc[-1])
    return_pct = ((current_value / total_invested) - 1) * 100 if total_invested > 0 else 0
    return {
        "units": round(total_units, 4),
        "invested": round(total_invested, 2),
        "current_value": round(current_value, 2),
        "return_pct": round(return_pct, 2),
    }
