import sys
import json
from datetime import datetime
from typing import Dict, Any, List
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    DISCORD_WEBHOOK_URL,
    DISCORD_BOT_TOKEN,
    DISCORD_CHANNEL_ID,
    JOBPOL_URL,
    LOGO_FILE,
    LANGUAGE,
)
from translations import get_text

POLICE_BLUE = 0x0055AA
SUCCESS_GREEN = 0x2ECC71


def _send_payload(payload: dict) -> bool:
    has_logo = LOGO_FILE.exists()

    if DISCORD_WEBHOOK_URL and not DISCORD_WEBHOOK_URL.endswith("YOUR_WEBHOOK_URL_HERE"):
        try:
            if has_logo:
                with open(LOGO_FILE, "rb") as f:
                    files = {"files[0]": ("logo_police.png", f, "image/png")}
                    data = {"payload_json": json.dumps(payload)}
                    resp = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=15)
            else:
                resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)

            if resp.status_code in (200, 204):
                return True
            print(f"Discord Webhook error (HTTP {resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            print(f"Discord Webhook request failed: {e}")
            return False

    if DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID:
        try:
            url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
            headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
            if has_logo:
                with open(LOGO_FILE, "rb") as f:
                    files = {"files[0]": ("logo_police.png", f, "image/png")}
                    data = {"payload_json": json.dumps(payload)}
                    resp = requests.post(url, data=data, files=files, headers=headers, timeout=15)
            else:
                headers["Content-Type"] = "application/json"
                resp = requests.post(url, json=payload, headers=headers, timeout=10)

            if resp.status_code in (200, 201):
                return True
            print(f"Discord Bot error (HTTP {resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            print(f"Discord Bot request failed: {e}")
            return False

    return False


def notify_new_job(job: Dict[str, Any]) -> bool:
    title = job.get("title") or get_text("not_specified", LANGUAGE)
    zone = job.get("zone") or get_text("not_specified", LANGUAGE)
    deadline = job.get("deadline") or get_text("not_specified", LANGUAGE)
    link = job.get("url") or JOBPOL_URL

    embed = {
        "title": get_text("discord_job_title", LANGUAGE, title=title),
        "url": link,
        "description": get_text("discord_job_desc", LANGUAGE),
        "color": POLICE_BLUE,
        "thumbnail": {"url": "attachment://logo_police.png"} if LOGO_FILE.exists() else {},
        "fields": [
            {"name": get_text("discord_field_zone", LANGUAGE), "value": zone, "inline": True},
            {"name": get_text("discord_field_deadline", LANGUAGE), "value": deadline, "inline": True},
            {"name": get_text("discord_field_link", LANGUAGE), "value": f"[{get_text('discord_link_text', LANGUAGE)}]({link})", "inline": False},
        ],
        "footer": {"text": get_text("discord_footer", LANGUAGE)},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    payload = {
        "username": "Jobpol Reserve Notifier",
        "embeds": [embed],
    }

    success = _send_payload(payload)
    if success:
        print(f"Discord notification delivered: {title}")
    return success


def notify_multiple_jobs(jobs: List[Dict[str, Any]]) -> int:
    sent_count = 0
    for job in jobs:
        if notify_new_job(job):
            sent_count += 1
    return sent_count


def send_test_notification() -> bool:
    embed = {
        "title": get_text("discord_test_title", LANGUAGE),
        "description": get_text("discord_test_desc", LANGUAGE),
        "color": SUCCESS_GREEN,
        "thumbnail": {"url": "attachment://logo_police.png"} if LOGO_FILE.exists() else {},
        "fields": [
            {"name": "Status", "value": get_text("discord_test_status", LANGUAGE), "inline": True},
            {"name": get_text("discord_test_time", LANGUAGE), "value": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "inline": True},
        ],
        "footer": {"text": get_text("discord_footer", LANGUAGE)},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    payload = {
        "username": "Jobpol Reserve Notifier",
        "embeds": [embed],
    }

    return _send_payload(payload)
