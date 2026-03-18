"""
QUICK SETUP — Choose your notification method and go!
Run: python setup_alerts.py
"""
import os
import sys
import subprocess

PYTHON = sys.executable or r"C:\Users\theya\AppData\Local\Programs\Python\Python310\python.exe"

print("""
╔══════════════════════════════════════════════════════╗
║   🎯 WAR-ERA PRICE ALERT — SETUP WIZARD             ║
║   Gold & Silver Dip Notifications                    ║
╚══════════════════════════════════════════════════════╝

Choose notification method:

  [1] TELEGRAM BOT (Recommended — instant, free, works when PC off)
      → Takes 2 minutes to setup
      → Get alerts on your phone 24/7

  [2] WINDOWS NOTIFICATIONS ONLY (PC must be on)
      → No setup needed — start immediately
      → Runs as background service via Task Scheduler

  [3] TEST — Send a test notification right now

  [4] START LOCAL MONITORING (runs in background)

  [5] INSTALL AS WINDOWS TASK (runs even after reboot)
""")

choice = input("Enter choice (1-5): ").strip()

if choice == "1":
    print("""
    TELEGRAM SETUP (2 minutes):
    ═══════════════════════════
    1. Open Telegram on your phone
    2. Search for @BotFather → Send /newbot
    3. Name: WarEraAlerts → Username: warera_alerts_bot (or similar)
    4. Copy the BOT TOKEN it gives you
    5. Search for @userinfobot → Send /start → Copy your CHAT ID
    """)
    token = input("Paste BOT TOKEN: ").strip()
    chat_id = input("Paste CHAT ID: ").strip()

    if token and chat_id:
        # Update cloud_alert.py
        alert_file = os.path.join(os.path.dirname(__file__), "cloud_alert.py")
        content = open(alert_file, "r").read()
        content = content.replace("YOUR_BOT_TOKEN_HERE", token)
        content = content.replace("YOUR_CHAT_ID_HERE", chat_id)
        open(alert_file, "w").write(content)
        print("\n✅ Telegram configured! Sending test...")
        subprocess.run([PYTHON, alert_file, "--test"])
        print("\nCheck your Telegram for the test message!")
        print(f"\nTo start monitoring: python cloud_alert.py")
    else:
        print("Missing token or chat ID.")

elif choice == "2":
    print("\nStarting Windows notification monitor...")
    alert_file = os.path.join(os.path.dirname(__file__), "price_alert.py")
    subprocess.Popen(
        [PYTHON, alert_file],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    print("✅ Running in background! You'll get Windows toast notifications on dips.")

elif choice == "3":
    print("\nSending test notification...")
    alert_file = os.path.join(os.path.dirname(__file__), "cloud_alert.py")
    subprocess.run([PYTHON, alert_file, "--test"])

elif choice == "4":
    print("\nStarting continuous monitoring...")
    alert_file = os.path.join(os.path.dirname(__file__), "cloud_alert.py")
    subprocess.run([PYTHON, alert_file])

elif choice == "5":
    print("\nInstalling Windows Scheduled Task...")
    alert_file = os.path.join(os.path.dirname(__file__), "cloud_alert.py")
    task_name = "WarEraPriceAlert"

    # Create task that runs every 15 minutes
    cmd = (
        f'schtasks /create /tn "{task_name}" /tr '
        f'"\"{PYTHON}\" \"{alert_file}\" --once" '
        f'/sc minute /mo 15 /f'
    )
    result = os.system(cmd)
    if result == 0:
        print(f"""
✅ Scheduled Task Created: {task_name}
   Runs every 15 minutes, even after reboot!

   To remove: schtasks /delete /tn "{task_name}" /f
   To check:  schtasks /query /tn "{task_name}"
        """)
    else:
        print("Failed — try running as Administrator")

else:
    print("Invalid choice.")
