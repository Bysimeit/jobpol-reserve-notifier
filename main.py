import argparse
import sys
import time
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from colorama import init, Fore, Style

from config import (
    validate_config,
    CHECK_INTERVAL_MINUTES,
    STORAGE_FILE,
    LANGUAGE,
)
from scraper import scrape_jobpol_reserve
from storage import filter_new_jobs, record_jobs
from notifier import notify_multiple_jobs, send_test_notification
from translations import get_text

init(autoreset=True)


def print_banner():
    title = get_text("banner_title", LANGUAGE)
    border = "=" * (len(title) + 8)
    print(f"\n{Fore.BLUE}{border}\n   {title}\n{border}{Style.RESET_ALL}\n")


def run_check(headed: bool = False) -> None:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{timestamp}] {get_text('checking_page', LANGUAGE)}")

    jobs = scrape_jobpol_reserve(headless=not headed)

    if not jobs:
        print(f"info: {get_text('no_jobs_found', LANGUAGE)}")
        return

    new_jobs = filter_new_jobs(jobs)

    if not new_jobs:
        print(f"{Fore.GREEN}{get_text('up_to_date', LANGUAGE, count=len(jobs))}{Style.RESET_ALL}")
        record_jobs(jobs)
        return

    print(f"{Fore.YELLOW}{get_text('new_jobs_detected', LANGUAGE, count=len(new_jobs))}{Style.RESET_ALL}")
    for j in new_jobs:
        zone_label = j.get('zone') or get_text('not_specified', LANGUAGE)
        print(f"  {j.get('title')} ({zone_label})")

    sent = notify_multiple_jobs(new_jobs)
    print(get_text("notifications_sent", LANGUAGE, sent=sent, total=len(new_jobs)))

    record_jobs(new_jobs)
    print(get_text("storage_updated", LANGUAGE))


def run_watch(interval_minutes: int, headed: bool = False) -> None:
    print(f"{Fore.CYAN}{get_text('watch_mode_active', LANGUAGE, interval=interval_minutes)}{Style.RESET_ALL}")
    print(f"{get_text('stop_hint', LANGUAGE)}\n")

    while True:
        try:
            run_check(headed=headed)
            print(f"\n{get_text('next_check', LANGUAGE, interval=interval_minutes)}")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print(f"\n{get_text('stopping', LANGUAGE)}")
            sys.exit(0)
        except Exception as e:
            print(f"{Fore.RED}{get_text('error_cycle', LANGUAGE, error=e)}{Style.RESET_ALL}")
            print(get_text("retry_soon", LANGUAGE))
            time.sleep(300)


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Monitor Jobpol recruitment reserve and notify Discord.")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL_MINUTES, help="Check interval in minutes")
    parser.add_argument("--headed", action="store_true", help="Show browser window for debugging")
    parser.add_argument("--test-discord", action="store_true", help="Send test notification to Discord")
    parser.add_argument("--reset", action="store_true", help="Reset local storage of seen jobs")
    args = parser.parse_args()

    if args.test_discord:
        if not validate_config(require_password=False):
            sys.exit(1)
        success = send_test_notification()
        if success:
            print(get_text("discord_test_success", LANGUAGE))
        else:
            print(get_text("discord_test_failed", LANGUAGE))
        return

    if args.reset:
        if STORAGE_FILE.exists():
            STORAGE_FILE.unlink()
            print(f"Storage file {STORAGE_FILE.name} removed.")
        return

    if not validate_config(require_password=True):
        sys.exit(1)

    if args.watch:
        run_watch(args.interval, headed=args.headed)
    else:
        run_check(headed=args.headed)


if __name__ == "__main__":
    main()
