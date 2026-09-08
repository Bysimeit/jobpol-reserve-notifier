import hashlib
import sys
import time
from urllib.parse import urljoin
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from config import (
    JOBPOL_URL,
    JOBPOL_PASSWORD,
    HEADLESS,
    DEBUG,
    DEBUG_DIR,
    LANGUAGE,
)
from translations import get_text


def _generate_job_id(title: str, link: str, zone: str = "") -> str:
    raw = f"{title.strip().lower()}|{link.strip().lower()}|{zone.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def scrape_jobpol_reserve(headless: bool = None) -> List[Dict[str, Any]]:
    if headless is None:
        headless = HEADLESS

    jobs: List[Dict[str, Any]] = []

    print(get_text("launching_browser", LANGUAGE, headless=headless))

    with sync_playwright() as p:
        browser = None
        for ch in ["chrome", None]:
            try:
                launch_kwargs = {
                    "headless": headless,
                    "ignore_default_args": ["--enable-automation"],
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-infobars",
                    ],
                }
                if ch:
                    launch_kwargs["channel"] = ch
                browser = p.chromium.launch(**launch_kwargs)
                break
            except Exception:
                continue

        if not browser:
            browser = p.chromium.launch(headless=headless)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="nl-BE" if LANGUAGE == "NL" else "fr-BE",
        )

        page = context.new_page()
        page.add_init_script("delete Object.getPrototypeOf(navigator).webdriver;")
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        try:
            print(get_text("navigating", LANGUAGE, url=JOBPOL_URL))
            page.goto(JOBPOL_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2000)

            try:
                cookie_btn = page.locator(".cookie-consent button, .js-cookie-bar button, button:has-text('Accepter'), button:has-text('Accepteren')").first
                if cookie_btn.count() > 0 and cookie_btn.is_visible(timeout=1500):
                    print(get_text("cookie_banner", LANGUAGE))
                    cookie_btn.click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            pwd_input = page.locator("input[type='password'], input#edit-password, input[name*='pass']").first
            if pwd_input.count() > 0 and pwd_input.is_visible(timeout=2000):
                print(get_text("password_form", LANGUAGE))
                if not JOBPOL_PASSWORD:
                    print(get_text("no_password_set", LANGUAGE))
                else:
                    pwd_input.fill(JOBPOL_PASSWORD)
                    page.wait_for_timeout(300)
                    pwd_input.press("Enter")
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    page.wait_for_timeout(3000)
                    print(get_text("form_submitted", LANGUAGE))

            if DEBUG:
                screenshot_path = DEBUG_DIR / "jobpol_page.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                html_path = DEBUG_DIR / "jobpol_page.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(page.content())

            print(get_text("extracting_jobs", LANGUAGE))

            page_index = 1
            max_pages = 25

            while page_index <= max_pages:
                tiles = page.locator(".tile--vacancy-overview, .views-row .tile").all()
                if tiles:
                    for tile in tiles:
                        link_elem = tile.locator("a.tile__inner, a").first
                        href = link_elem.get_attribute("href") if link_elem.count() > 0 else ""
                        url = urljoin(JOBPOL_URL, href)

                        title_inner = tile.locator(".tile__title__inner").first
                        if title_inner.count() > 0:
                            title = title_inner.inner_text().strip()
                        else:
                            title_elem = tile.locator(".tile__title, h3").first
                            title = title_elem.inner_text().strip() if title_elem.count() > 0 else "Poste Jobpol"

                        loc_elem = tile.locator(".tile__title--zip").first
                        zone = loc_elem.inner_text().strip() if loc_elem.count() > 0 else ""

                        date_elem = tile.locator(".tile__title--register_date, .tile__title--register").first
                        deadline = date_elem.inner_text().strip() if date_elem.count() > 0 else ""

                        if title:
                            job_id = _generate_job_id(title, url, zone)
                            if not any(existing.get("id") == job_id for existing in jobs):
                                jobs.append({
                                    "id": job_id,
                                    "title": title,
                                    "zone": zone,
                                    "deadline": deadline,
                                    "url": url,
                                })

                if not jobs:
                    rows = page.locator("table tbody tr, .views-table tbody tr").all()
                    if rows:
                        for row in rows:
                            text = row.inner_text().strip()
                            if not text:
                                continue
                            link_elem = row.locator("a").first
                            url = urljoin(JOBPOL_URL, link_elem.get_attribute("href")) if link_elem.count() > 0 else JOBPOL_URL
                            cols = [c.inner_text().strip() for c in row.locator("td").all()]

                            title = cols[0] if len(cols) > 0 else text.split("\n")[0]
                            zone = cols[1] if len(cols) > 1 else ""
                            deadline = cols[2] if len(cols) > 2 else ""

                            job_id = _generate_job_id(title, url, zone)
                            if not any(existing.get("id") == job_id for existing in jobs):
                                jobs.append({
                                    "id": job_id,
                                    "title": title,
                                    "zone": zone,
                                    "deadline": deadline,
                                    "url": url,
                                })

                next_btn = page.locator(".pager__item--next a, a[rel='next']").first
                if next_btn.count() > 0 and next_btn.is_visible(timeout=1500):
                    next_btn.click()
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    page.wait_for_timeout(2500)
                    page_index += 1
                else:
                    break

            print(get_text("jobs_found", LANGUAGE, count=len(jobs)))

        except PlaywrightTimeoutError as te:
            print(get_text("timeout_error", LANGUAGE, error=te))
            try:
                page.screenshot(path=str(DEBUG_DIR / "timeout_error.png"))
            except Exception:
                pass
        except Exception as e:
            print(get_text("unexpected_error", LANGUAGE, error=e))
            try:
                page.screenshot(path=str(DEBUG_DIR / "error_page.png"))
            except Exception:
                pass
        finally:
            browser.close()

    return jobs
