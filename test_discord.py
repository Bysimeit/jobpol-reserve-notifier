import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from notifier import send_test_notification
from config import validate_config, LANGUAGE
from translations import get_text

if __name__ == "__main__":
    if not validate_config(require_password=False):
        sys.exit(1)

    success = send_test_notification()
    if success:
        print(f"\n{get_text('discord_test_success', LANGUAGE)}")
    else:
        print(f"\n{get_text('discord_test_failed', LANGUAGE)}")
