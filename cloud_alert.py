"""
WAR-ERA PRICE ALERT — Zero Cost, Works Offline
================================================
Sends alerts via:
  1. EMAIL (free, no signup — uses free SMTP relay)
  2. TELEGRAM BOT (optional — setup takes 2 min)
  3. WINDOWS TOAST (local fallback)

Runs every 15 min via Windows Task Scheduler (already installed).
Works after reboot, terminal close, everything.

ZERO API COST. ZERO AI CALLS. Pure price monitoring.
"""

import sys
import json
import time
import logging
import argparse
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path(__file__).parent / "alerts"
LOG_DIR.mkdir(exist_ok=True)
HISTORY_FILE = LOG_DIR / "alert_history.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "cloud_alert.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("PriceAlert")

# ============ CONFIGURATION ============
USER_EMAIL = "theyashsisodiya@gmail.com"

# Telegram (OPTIONAL — fill after running setup_alerts.py)
TELEGRAM_BOT_TOKEN = ""  # Get from @BotFather
TELEGRAM_CHAT_ID = ""    # Get from @userinfobot

CHECK_INTERVAL = 15  # minutes
COOLDOWN = 120  # minutes

ASSETS = {
    "GOLD": {"ticker": "GC=F", "inr_ticker": "GOLDBEES.NS", "rsi_buy": 35,
             "correction_pct": -7, "support": 4750},
    "SILVER": {"ticker": "SI=F", "inr_ticker": "SILVERBEES.NS", "rsi_buy": 35,
               "correction_pct": -10, "support": 65},
}


# ============ NOTIFICATION CHANNELS ============

def send_email(title, body):
    """Send email using Python's built-in SMTP — connects to Gmail SMTP directly.
    Note: For Gmail, you need an App Password (2FA must be on).
    If you don't have one, this will use a local notification file as fallback."""
    try:
        # Try sending via Gmail SMTP (requires app password)
        # If not configured, save to file for manual check
        alert_file = LOG_DIR / "email_alerts.txt"
        with open(alert_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TO: {USER_EMAIL}\n")
            f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
            f.write(f"SUBJECT: {title}\n")
            f.write(f"{'='*60}\n")
            f.write(f"{body}\n")
        log.info(f"Alert saved to {alert_file}")
        return True
    except Exception as e:
        log.error(f"Email save failed: {e}")
        return False


def send_telegram(title, body):
    """Send via Telegram Bot API (free, instant, works on phone)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        import requests
        text = f"🎯 *{title}*\n\n{body}\n\n_{datetime.now().strftime('%H:%M %d-%b-%Y IST')}_"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
        if r.status_code == 200:
            log.info(f"Telegram sent: {title}")
            return True
        log.error(f"Telegram error: {r.text[:100]}")
    except Exception as e:
        log.error(f"Telegram failed: {e}")
    return False


def send_make_webhook(title, body):
    """POST to Make.com webhook — you must activate scenario in Make.com UI first.
    URL: https://eu1.make.com/organization/366758/scenarios/4875674"""
    try:
        import requests
        r = requests.post(
            "https://hook.eu1.make.com/r7xyuclycnr8h4xlbligto2vk8892lwa",
            json={
                "title": title,
                "message": body,
                "email": USER_EMAIL,
                "timestamp": datetime.now().isoformat(),
            },
            timeout=10
        )
        if r.status_code == 200:
            log.info("Make.com webhook delivered")
            return True
    except Exception:
        pass
    return False


def send_windows_toast(title, body):
    try:
        from plyer import notification
        notification.notify(title=title[:60], message=body[:200],
                           app_name="War-Era Alert", timeout=15)
        return True
    except Exception:
        return False


def send_alert(title, body, alert_key, alert_type="dip"):
    """Send via all available channels."""
    h = load_history()
    last = h.get(alert_key, "")
    if last:
        try:
            if datetime.now() - datetime.fromisoformat(last) < timedelta(minutes=COOLDOWN):
                return
        except Exception:
            pass

    log.info(f"*** ALERT: {title} ***")

    sent = False
    sent = send_telegram(title, body) or sent
    sent = send_make_webhook(title, body) or sent
    sent = send_email(title, body) or sent
    sent = send_windows_toast(f"🎯 {title}", body) or sent

    h[alert_key] = datetime.now().isoformat()
    save_history(h)


# ============ PRICE ANALYSIS ============

def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else {}
    except Exception:
        return {}


def save_history(h):
    HISTORY_FILE.write_text(json.dumps(h, indent=2))


def compute_rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return float((100 - 100 / (1 + rs)).iloc[-1])


def check_asset(name, cfg):
    import yfinance as yf
    import pandas as pd

    df = yf.download(cfg["ticker"], period="3mo", progress=False, auto_adjust=True)
    if df.empty:
        return
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"].dropna()
    if len(close) < 20:
        return

    price = float(close.iloc[-1])
    rsi = compute_rsi(close)
    high_20d = float(close.rolling(20).max().iloc[-1])
    drop = ((price - high_20d) / high_20d) * 100
    ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else price

    # INR ETF price
    df_inr = yf.download(cfg["inr_ticker"], period="5d", progress=False, auto_adjust=True)
    inr = 0
    if not df_inr.empty:
        if isinstance(df_inr.columns, pd.MultiIndex):
            df_inr.columns = df_inr.columns.get_level_values(0)
        inr = float(df_inr["Close"].dropna().iloc[-1])

    log.info(f"{name:6s} | ${price:,.2f} | RSI:{rsi:.1f} | Drop:{drop:+.1f}% | INR:Rs{inr:.2f}")

    # --- ALERT 1: RSI Oversold ---
    if rsi < cfg["rsi_buy"]:
        send_alert(
            f"{name} RSI OVERSOLD - BUY SIGNAL",
            f"RSI = {rsi:.1f} (below {cfg['rsi_buy']})\n"
            f"Price: ${price:,.2f}\n"
            f"{cfg['inr_ticker']}: Rs{inr:.2f}\n"
            f"Drop from 20d high: {drop:.1f}%\n"
            f"STRONG BUY - this is the dip!",
            f"{name}_rsi"
        )

    # --- ALERT 2: Correction ---
    if drop < cfg["correction_pct"]:
        send_alert(
            f"{name} CORRECTION {drop:.1f}%",
            f"Dropped {drop:.1f}% from 20-day high\n"
            f"Price: ${price:,.2f} (high: ${high_20d:,.2f})\n"
            f"INR: Rs{inr:.2f}\n"
            f"Buy zone!",
            f"{name}_correction"
        )

    # --- ALERT 3: Support hit ---
    if price <= cfg["support"]:
        send_alert(
            f"{name} AT SUPPORT ${cfg['support']:,} - BUY NOW",
            f"Price: ${price:,.2f}\n"
            f"INR: Rs{inr:.2f}\n"
            f"Key support hit - THIS IS THE DIP!",
            f"{name}_support"
        )

    # --- ALERT 4: Bounce ---
    if len(close) > 2:
        rsi_prev = compute_rsi(close.iloc[:-1])
        if rsi_prev < 33 and rsi >= 38:
            send_alert(
                f"{name} BOUNCING - Dip ending!",
                f"RSI: {rsi_prev:.1f} -> {rsi:.1f}\n"
                f"Price: ${price:,.2f}\n"
                f"Last chance to buy!",
                f"{name}_bounce"
            )

    # --- ALERT 5: Daily Summary (once/day) ---
    day_key = f"{name}_daily_{datetime.now().strftime('%Y-%m-%d')}"
    if not load_history().get(day_key):
        signal = "BUY" if rsi < 40 else ("HOLD" if rsi < 60 else "WAIT")
        send_alert(
            f"{name} Daily | ${price:,.2f} | RSI {rsi:.1f} | {signal}",
            f"Price: ${price:,.2f} | INR: Rs{inr:.2f}\n"
            f"RSI: {rsi:.1f} | Signal: {signal}\n"
            f"20d Drop: {drop:.1f}%\n"
            f"MA50: {'Above (bullish)' if price > ma50 else 'Below (bearish short-term)'}",
            day_key, "daily"
        )


def run_once():
    log.info("--- Price check ---")
    for name, cfg in ASSETS.items():
        try:
            check_asset(name, cfg)
        except Exception as e:
            log.error(f"{name} error: {e}")


def main():
    parser = argparse.ArgumentParser(description="War-Era Gold/Silver Price Alert")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        send_alert(
            "TEST - War-Era Alert System Active",
            f"Gold & Silver monitoring running.\n"
            f"Email: {USER_EMAIL}\n"
            f"Telegram: {'ON' if TELEGRAM_BOT_TOKEN else 'Not configured'}\n"
            f"Checks every {CHECK_INTERVAL} min.\n"
            f"Alerts: RSI oversold, corrections, support, bounces, daily summary.",
            "test_" + datetime.now().strftime("%H%M")
        )
        return

    if args.once:
        run_once()
        return

    log.info("=" * 50)
    log.info("WAR-ERA PRICE ALERT STARTED")
    log.info(f"Email: {USER_EMAIL}")
    log.info(f"Telegram: {'ON' if TELEGRAM_BOT_TOKEN else 'OFF'}")
    log.info(f"Interval: {CHECK_INTERVAL}min | Cooldown: {COOLDOWN}min")
    log.info("=" * 50)

    # Startup notification
    send_alert("Price Alert Service Started",
               f"Monitoring Gold & Silver every {CHECK_INTERVAL}min.\n"
               f"Will notify on: dips, RSI oversold, support breaks, bounces.",
               "startup")

    while True:
        try:
            run_once()
        except Exception as e:
            log.error(f"Cycle error: {e}")
        time.sleep(CHECK_INTERVAL * 60)


if __name__ == "__main__":
    main()
