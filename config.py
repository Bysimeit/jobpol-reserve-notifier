import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from translations import get_text

BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

LANGUAGE = os.getenv("LANGUAGE", "EN").strip().upper()
if LANGUAGE not in ("EN", "NL", "FR", "DE"):
    LANGUAGE = "EN"

DEFAULT_URLS = {
    "NL": "https://www.jobpol.be/nl/wervingsreserve",
    "FR": "https://www.jobpol.be/fr/reserve-de-recrutement",
    "DE": "https://www.jobpol.be/fr/reserve-de-recrutement",
    "EN": "https://www.jobpol.be/fr/reserve-de-recrutement",
}

JOBPOL_URL = os.getenv("JOBPOL_URL", "").strip() or DEFAULT_URLS.get(LANGUAGE, DEFAULT_URLS["EN"])
JOBPOL_PASSWORD = os.getenv("JOBPOL_PASSWORD", "").strip()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID", "").strip()

FILTER_UNIT = os.getenv("FILTER_UNIT", "").strip() or os.getenv("FILTER_UNITS", "").strip()
FILTER_GRADE = os.getenv("FILTER_GRADE", "").strip() or os.getenv("FILTER_GRADES", "").strip()
FILTER_REGION = os.getenv("FILTER_REGION", "").strip() or os.getenv("FILTER_REGIONS", "").strip()

try:
    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
except ValueError:
    CHECK_INTERVAL_MINUTES = 30

HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes", "y")
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "y")

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_FILE = DATA_DIR / "seen_jobs.json"

LOGO_FILE = BASE_DIR / "logo_police.png"
DEBUG_DIR = BASE_DIR / "debug"
DEBUG_DIR.mkdir(exist_ok=True)


def validate_config(require_password: bool = True) -> bool:
    errors = []

    if require_password and not JOBPOL_PASSWORD:
        errors.append(get_text("cfg_error_password", LANGUAGE))

    has_webhook = bool(DISCORD_WEBHOOK_URL and not DISCORD_WEBHOOK_URL.endswith("YOUR_WEBHOOK_URL_HERE"))
    has_bot = bool(DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID)

    if not (has_webhook or has_bot):
        errors.append(get_text("cfg_error_discord", LANGUAGE))

    if errors:
        print(f"\n{get_text('cfg_error_title', LANGUAGE)}")
        for err in errors:
            print(f"  • {err}")
        print(f"\n{get_text('cfg_tip', LANGUAGE)}\n")
        return False

    return True
