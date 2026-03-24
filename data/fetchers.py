"""Data fetching layer — all external API calls centralized here."""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import feedparser
import streamlit as st
import json
import logging
import io
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

PRICE_CACHE_PATH = Path(__file__).parent.parent / "alerts" / "price_cache.json"

# --- Source Health Tracking ---
_source_health = {
    "yfinance": {"ok": True, "fail_count": 0, "skip_until": None},
    "stooq": {"ok": True, "fail_count": 0, "skip_until": None},
}


def _is_source_available(name: str) -> bool:
    """Check if a data source should be attempted (auto-skip after 3 failures)."""
    h = _source_health.get(name, {"ok": True, "skip_until": None})
    if h.get("skip_until") and datetime.now() < h["skip_until"]:
        return False
    return True


def _record_failure(name: str) -> None:
    """Record a source failure; skip source for 10 min after 3 consecutive failures."""
    h = _source_health.setdefault(name, {"ok": True, "fail_count": 0, "skip_until": None})
    h["fail_count"] = h.get("fail_count", 0) + 1
    if h["fail_count"] >= 3:
        h["ok"] = False
        h["skip_until"] = datetime.now() + timedelta(minutes=10)
        logger.warning("Source %s disabled for 10 min after %d failures", name, h["fail_count"])


def _record_success(name: str) -> None:
    """Reset source health on success."""
    _source_health[name] = {"ok": True, "fail_count": 0, "skip_until": None}


def get_source_health() -> dict:
    """Get current health status of all data sources (for UI display)."""
    return {
        name: {"ok": h.get("ok", True), "fail_count": h.get("fail_count", 0)}
        for name, h in _source_health.items()
    }


def _load_price_cache() -> dict:
    """Load last-known prices from disk cache."""
    try:
        if PRICE_CACHE_PATH.exists():
            return json.loads(PRICE_CACHE_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_price_cache(cache: dict) -> None:
    """Persist price cache to disk."""
    try:
        PRICE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PRICE_CACHE_PATH.write_text(json.dumps(cache))
    except Exception:
        pass


def get_cached_with_age(ticker: str) -> tuple:
    """Returns (cached_data, hours_old) for stale cache detection."""
    cache = _load_price_cache()
    entry = cache.get(ticker, {})
    if not entry or entry.get("price", 0) <= 0:
        return {"price": 0, "change_pct": 0, "prev_close": 0}, float("inf")
    cached_at_str = entry.get("cached_at", "2000-01-01T00:00:00")
    try:
        cached_at = datetime.fromisoformat(cached_at_str)
    except (ValueError, TypeError):
        cached_at = datetime(2000, 1, 1)
    hours_old = (datetime.now() - cached_at).total_seconds() / 3600
    return entry, hours_old


def _stooq_ticker(ticker: str) -> str:
    """Convert yfinance ticker to stooq format (e.g. GOLDBEES.NS → goldbees.in)."""
    t = ticker.lower()
    if t.endswith(".ns") or t.endswith(".bo"):
        return t.rsplit(".", 1)[0] + ".in"
    if t.startswith("^"):
        return t[1:]
    return t


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_stooq_ohlcv(ticker: str, period_days: int = 365) -> pd.DataFrame:
    """Fetch OHLCV data from stooq.com CSV API as fallback."""
    try:
        stooq_sym = _stooq_ticker(ticker)
        end = datetime.now()
        start = end - timedelta(days=period_days)
        url = (
            f"https://stooq.com/q/d/l/"
            f"?s={stooq_sym}"
            f"&d1={start.strftime('%Y%m%d')}"
            f"&d2={end.strftime('%Y%m%d')}"
            f"&i=d"
        )
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200 or "No data" in resp.text[:50]:
            return pd.DataFrame()
        df = pd.read_csv(io.StringIO(resp.text), parse_dates=["Date"], index_col="Date")
        df = df.sort_index()
        if df.empty or "Close" not in df.columns:
            return pd.DataFrame()
        logger.info("stooq fallback succeeded for %s", ticker)
        return df
    except Exception as e:
        logger.debug("stooq fallback failed for %s: %s", ticker, e)
        return pd.DataFrame()


PERIOD_TO_DAYS = {
    "5d": 10, "1mo": 35, "2mo": 70, "3mo": 100,
    "6mo": 200, "1y": 370, "2y": 740, "5y": 1850, "max": 3650,
}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_etf_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch OHLCV data for a single ETF. Auto-skips broken sources."""
    # Tier 1: yfinance
    if _is_source_available("yfinance"):
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.loc[:, ~df.columns.duplicated()]
                _record_success("yfinance")
                return df
            _record_failure("yfinance")
        except Exception as e:
            _record_failure("yfinance")
            logger.warning("yfinance failed for %s: %s", ticker, e)

    # Tier 2: stooq
    if _is_source_available("stooq"):
        try:
            days = PERIOD_TO_DAYS.get(period, 370)
            df = _fetch_stooq_ohlcv(ticker, period_days=days)
            if not df.empty:
                _record_success("stooq")
                return df
            _record_failure("stooq")
        except Exception as e:
            _record_failure("stooq")
            logger.warning("stooq failed for %s: %s", ticker, e)

    return pd.DataFrame()


def _extract_price_from_df(ticker_df: pd.DataFrame) -> dict:
    """Extract latest price, daily change percentage, and previous close from OHLCV data.

    Returns a dict with keys: price, change_pct, prev_close.
    Returns zeroed dict if the DataFrame has no valid close prices.
    """
    if ticker_df.empty or "Close" not in ticker_df.columns:
        return {"price": 0, "change_pct": 0, "prev_close": 0}
    ticker_df = ticker_df.dropna(subset=["Close"])
    if len(ticker_df) < 1:
        return {"price": 0, "change_pct": 0, "prev_close": 0}
    close_today = float(ticker_df["Close"].iloc[-1])
    close_prev = float(ticker_df["Close"].iloc[-2]) if len(ticker_df) > 1 else close_today
    change_pct = ((close_today - close_prev) / close_prev) * 100 if close_prev else 0
    return {
        "price": round(close_today, 2),
        "change_pct": round(change_pct, 2),
        "prev_close": round(close_prev, 2),
    }


def _fetch_single_stooq_price(ticker: str) -> dict:
    """Fetch price for a single ticker via stooq fallback."""
    df = _fetch_stooq_ohlcv(ticker, period_days=10)
    if df.empty:
        return {"price": 0, "change_pct": 0, "prev_close": 0}
    return _extract_price_from_df(df)


@st.cache_data(ttl=300, show_spinner="Fetching prices...")
def fetch_batch_prices(tickers: tuple) -> dict:
    """Batch price fetch: yfinance → stooq → disk cache. Auto-skips broken sources."""
    results = {}
    sources_used = {}
    failed_tickers = list(tickers)

    # --- Tier 1: yfinance batch ---
    if _is_source_available("yfinance"):
        try:
            df = yf.download(list(tickers), period="5d", progress=False,
                             auto_adjust=True, group_by="ticker", threads=True)
            if not df.empty:
                for t in tickers:
                    try:
                        if len(tickers) == 1:
                            ticker_df = df
                            if isinstance(ticker_df.columns, pd.MultiIndex):
                                ticker_df.columns = ticker_df.columns.get_level_values(0)
                        else:
                            ticker_df = df[t]
                        result = _extract_price_from_df(ticker_df)
                        if result["price"] > 0:
                            results[t] = result
                            sources_used[t] = "yfinance"
                            continue
                    except Exception:
                        pass
                failed_tickers = [t for t in tickers if t not in results]
                if results:
                    _record_success("yfinance")
                if failed_tickers:
                    logger.info("yfinance missed %d tickers, trying stooq", len(failed_tickers))
            else:
                _record_failure("yfinance")
        except Exception as e:
            _record_failure("yfinance")
            logger.warning("yfinance batch failed: %s", e)

    # --- Tier 2: stooq individual fallback ---
    if failed_tickers and _is_source_available("stooq"):
        stooq_succeeded = False
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_map = {
                executor.submit(_fetch_single_stooq_price, t): t
                for t in failed_tickers
            }
            for future in as_completed(future_map):
                t = future_map[future]
                try:
                    result = future.result()
                    if result["price"] > 0:
                        results[t] = result
                        sources_used[t] = "stooq"
                        stooq_succeeded = True
                except Exception:
                    pass
        if stooq_succeeded:
            _record_success("stooq")
        else:
            _record_failure("stooq")

    # --- Tier 3: disk cache for anything still missing ---
    still_missing = [t for t in tickers if t not in results]
    if still_missing:
        cache = _load_price_cache()
        for t in still_missing:
            cached = cache.get(t)
            if cached and cached.get("price", 0) > 0:
                logger.info("[%s] using cached price", t)
                results[t] = {
                    "price": cached["price"],
                    "change_pct": cached.get("change_pct", 0),
                    "prev_close": cached.get("prev_close", 0),
                }
                sources_used[t] = "cache"
            else:
                results[t] = {"price": 0, "change_pct": 0, "prev_close": 0}

    # --- Persist successful fetches to cache ---
    cache = _load_price_cache()
    updated = False
    for t, data in results.items():
        if data["price"] > 0 and sources_used.get(t) != "cache":
            cache[t] = {
                **data,
                "source": sources_used.get(t, "unknown"),
                "cached_at": datetime.now().isoformat(),
            }
            updated = True
    if updated:
        _save_price_cache(cache)

    # Track primary source used for UI indicator
    if sources_used:
        primary = max(set(sources_used.values()), key=list(sources_used.values()).count)
        try:
            st.session_state["last_data_source"] = primary
        except Exception:
            pass

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
