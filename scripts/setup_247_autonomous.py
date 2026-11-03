"""
Setup script for 24/7 Autonomous Polya AI background runner with Epistemic Layer Separation.
"""

import os
import subprocess
from pathlib import Path

CRON_JOB = "*/15 * * * * cd /home/ubuntu/Polya-AI && /home/ubuntu/venv/bin/python .autonomous/orchestrator_daemon.py >> .autonomous/logs/cron_master.log 2>&1\n"

def install_cron():
    try:
        current_crontab = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    except Exception:
        current_crontab = ""

    if "orchestrator_daemon.py" in current_crontab:
        print("Cron job already installed.")
        return

    new_crontab = current_crontab.strip() + "\n" + CRON_JOB if current_crontab.strip() else CRON_JOB

    p = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
    if p.returncode == 0:
        print("Successfully installed 24/7 autonomous cron job (every 15 minutes).")
    else:
        print(f"Failed to install crontab: {p.stderr}")

if __name__ == "__main__":
    install_cron()
