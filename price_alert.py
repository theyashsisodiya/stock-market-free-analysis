"""
WAR-ERA PRICE ALERT — Gold & Silver Dip Notifier
=================================================
Runs silently in the background. Sends Windows notifications when:
- Gold/Silver RSI drops below 35 (oversold = BUY signal)
- Price drops below key support levels
- Price drops X% from recent high (correction detected)
- FOMC/ceasefire news keywords detected

Checks every 15 minutes. Survives terminal close via Task Scheduler.
"""
import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent / "alerts"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "alert_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("PriceAlert")

# ============ CONFIGURATION ============
CHECK_INTERVAL_MINUTES = 15
COOLDOWN_MINUTES = 120  # Don't repeat same alert for 2 hours

# Alert thresholds
ALERTS = {
    "GOLD": {
        "ticker": "GC=F",
        "inr_ticker": "GOLDBEES.NS",
        "name": "Gold",
        "rsi_buy": 35,           # RSI below this = BUY
        "correction_pct": -7,    # % drop from 20-day high = alert
        "support_usd": 4750,     # Key USD support level
        "support_inr": 115,      # GOLDBEES support
    },
    "SILVER": {
        "ticker": "SI=F",
        "inr_ticker": "SILVERBEES.NS",
        "name": "Silver",
        "rsi_buy": 35,
        "correction_pct": -10,
        "support_usd": 65,
        "support_inr": 200,
    },
}

NEWS_KEYWORDS = [
    "Fed rate cut", "FOMC", "ceasefire", "Iran deal",
    "gold crash", "silver crash", "precious metals sell",
    "rate decision", "gold correction", "silver drop",
]

# Track sent alerts to avoid spam
ALERT_HISTORY_FILE = LOG_DIR / "alert_history.json"


def load_alert_history():
    if ALERT_HISTORY_FILE.exists():
        try:
            return json.loads(ALERT_HISTORY_FILE.read_text())
        except Exception:
            pass
    return {}


def save_alert_history(history):
    ALERT_HISTORY_FILE.write_text(json.dumps(history, indent=2))


def should_send(alert_key, history):
    """Check cooldown — don't spam same alert."""
    last = history.get(alert_key, "")
    if not last:
        return True
    try:
        last_time = datetime.fromisoformat(last)
        return datetime.now() - last_time > timedelta(minutes=COOLDOWN_MINUTES)
    except Exception:
        return True


def send_notification(title, message, alert_key=""):
    """Send Windows toast notification."""
    try:
        from plyer import notification
        notification.notify(
            title=f"🎯 {title}",
            message=message,
            app_name="War-Era Price Alert",
            timeout=15,
        )
        log.info(f"ALERT SENT: {title} | {message}")

        # Update history
        history = load_alert_history()
        history[alert_key] = datetime.now().isoformat()
        save_alert_history(history)
    except Exception as e:
        log.error(f"Notification failed: {e}")


def compute_rsi(close, period=14):
    """Calculate RSI."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1])


def check_prices():
    """Main check — fetch data and evaluate alert conditions."""
    import yfinance as yf
    import pandas as pd

    history = load_alert_history()
    alerts_fired = []

    for key, cfg in ALERTS.items():
        try:
            # Fetch USD price
            df = yf.download(cfg["ticker"], period="3mo", progress=False, auto_adjust=True)
            if df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            close = df["Close"].dropna()
            if len(close) < 20:
                continue

            price = float(close.iloc[-1])
            rsi = compute_rsi(close)
            high_20d = float(close.rolling(20).max().iloc[-1])
            drop_from_high = ((price - high_20d) / high_20d) * 100

            # Also fetch INR ETF
            df_inr = yf.download(cfg["inr_ticker"], period="1mo", progress=False, auto_adjust=True)
            inr_price = 0
            if not df_inr.empty:
                if isinstance(df_inr.columns, pd.MultiIndex):
                    df_inr.columns = df_inr.columns.get_level_values(0)
                inr_price = float(df_inr["Close"].dropna().iloc[-1])

            log.info(
                f"{cfg['name']:6s} | ${price:,.2f} | RSI:{rsi:.1f} | "
                f"Drop:{drop_from_high:+.1f}% | {cfg['inr_ticker']}:₹{inr_price:.2f}"
            )

            # === ALERT 1: RSI Oversold ===
            if rsi < cfg["rsi_buy"]:
                alert_key = f"{key}_rsi_oversold"
                if should_send(alert_key, history):
                    send_notification(
                        f"{cfg['name']} RSI OVERSOLD — BUY SIGNAL",
                        f"RSI = {rsi:.1f} (below {cfg['rsi_buy']})\n"
                        f"Price: ${price:,.2f} | {cfg['inr_ticker']}: ₹{inr_price:.2f}\n"
                        f"Strong buy zone — dip detected!",
                        alert_key
                    )
                    alerts_fired.append(f"{key} RSI oversold")

            # === ALERT 2: Correction from 20-day high ===
            if drop_from_high < cfg["correction_pct"]:
                alert_key = f"{key}_correction"
                if should_send(alert_key, history):
                    send_notification(
                        f"{cfg['name']} CORRECTION {drop_from_high:.1f}%",
                        f"Dropped {drop_from_high:.1f}% from 20-day high\n"
                        f"Price: ${price:,.2f} | High was: ${high_20d:,.2f}\n"
                        f"Approaching buy zone!",
                        alert_key
                    )
                    alerts_fired.append(f"{key} correction")

            # === ALERT 3: Key support level ===
            if price <= cfg["support_usd"]:
                alert_key = f"{key}_support_usd"
                if should_send(alert_key, history):
                    send_notification(
                        f"{cfg['name']} AT SUPPORT — ${price:,.0f}",
                        f"Hit key support ${cfg['support_usd']:,}\n"
                        f"{cfg['inr_ticker']}: ₹{inr_price:.2f}\n"
                        f"STRONG BUY — this is the dip!",
                        alert_key
                    )
                    alerts_fired.append(f"{key} support hit")

            # === ALERT 4: INR ETF support ===
            if inr_price > 0 and inr_price <= cfg["support_inr"]:
                alert_key = f"{key}_support_inr"
                if should_send(alert_key, history):
                    send_notification(
                        f"{cfg['inr_ticker']} AT ₹{inr_price:.2f} — BUY",
                        f"Below support ₹{cfg['support_inr']}\n"
                        f"USD price: ${price:,.2f}\n"
                        f"Load up — historical support level!",
                        alert_key
                    )
                    alerts_fired.append(f"{key} INR support")

            # === ALERT 5: Bounce signal (RSI was oversold, now crossing 40) ===
            rsi_prev = compute_rsi(close.iloc[:-1])
            if rsi_prev < 35 and rsi >= 40:
                alert_key = f"{key}_bounce"
                if should_send(alert_key, history):
                    send_notification(
                        f"{cfg['name']} BOUNCING — Dip ending!",
                        f"RSI crossed 40 from oversold\n"
                        f"Price: ${price:,.2f}\n"
                        f"Bounce confirmed — last chance to buy the dip!",
                        alert_key
                    )
                    alerts_fired.append(f"{key} bounce")

        except Exception as e:
            log.error(f"Error checking {key}: {e}")

    # === NEWS ALERTS ===
    try:
        import feedparser
        for kw in NEWS_KEYWORDS[:5]:
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={kw.replace(' ', '+')}&hl=en&gl=US&ceid=US:en"
            )
            for entry in feed.entries[:2]:
                title = entry.get("title", "").lower()
                if any(trigger in title for trigger in ["crash", "plunge", "sell-off", "correction",
                                                          "ceasefire deal", "rate cut confirmed"]):
                    alert_key = f"news_{title[:30]}"
                    if should_send(alert_key, history):
                        send_notification(
                            "Market-Moving News Alert",
                            entry.get("title", "")[:100],
                            alert_key
                        )
                        alerts_fired.append("news")
                        break
    except Exception as e:
        log.error(f"News check failed: {e}")

    return alerts_fired


def main():
    log.info("=" * 50)
    log.info("WAR-ERA PRICE ALERT SERVICE STARTED")
    log.info(f"Checking every {CHECK_INTERVAL_MINUTES} minutes")
    log.info(f"Alert cooldown: {COOLDOWN_MINUTES} minutes")
    log.info("=" * 50)

    # Send startup notification
    send_notification(
        "Price Alert Active",
        f"Monitoring Gold & Silver every {CHECK_INTERVAL_MINUTES}min\n"
        f"Will notify on dips, RSI oversold, support breaks.",
        "startup"
    )

    while True:
        try:
            alerts = check_prices()
            if alerts:
                log.info(f"Alerts fired: {', '.join(alerts)}")
            else:
                log.info("No alerts triggered — all normal.")
        except Exception as e:
            log.error(f"Check cycle failed: {e}")

        # Sleep until next check
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
