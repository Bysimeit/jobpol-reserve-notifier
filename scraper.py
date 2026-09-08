import hashlib
import sys
from urllib.parse import urljoin
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from curl_cffi import requests
from bs4 import BeautifulSoup

from config import (
    JOBPOL_URL,
    JOBPOL_PASSWORD,
    DEBUG,
    DEBUG_DIR,
    LANGUAGE,
)
from translations import get_text


def _generate_job_id(title: str, link: str, zone: str = "") -> str:
    raw = f"{title.strip().lower()}|{link.strip().lower()}|{zone.strip().lower()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def scrape_jobpol_reserve(headless: bool = None) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []

    session = requests.Session(impersonate="chrome124")

    try:
        print(get_text("navigating", LANGUAGE, url=JOBPOL_URL))
        response = session.get(JOBPOL_URL, timeout=30)

        if response.status_code != 200:
            print(f"HTTP error {response.status_code}")
            return jobs

        soup = BeautifulSoup(response.text, "html.parser")
        form = (
            soup.find("form", id="password-authentication-form")
            or soup.find("form", class_="password-authentication-form")
            or soup.find("form", {"data-drupal-selector": "password-authentication-form"})
        )

        current_html = response.text
        current_url = response.url

        if form:
            print(get_text("password_form", LANGUAGE))
            if not JOBPOL_PASSWORD:
                print(get_text("no_password_set", LANGUAGE))
            else:
                action = form.get("action") or JOBPOL_URL
                post_url = urljoin(JOBPOL_URL, action)

                form_build_id = form.find("input", {"name": "form_build_id"})
                form_id = form.find("input", {"name": "form_id"})

                data = {
                    "password": JOBPOL_PASSWORD,
                    "op": "Se connecter",
                    "form_build_id": form_build_id.get("value", "") if form_build_id else "",
                    "form_id": form_id.get("value", "") if form_id else "password_authentication_form",
                }

                headers = {
                    "Referer": JOBPOL_URL,
                    "Origin": "https://www.jobpol.be",
                }

                auth_resp = session.post(post_url, data=data, headers=headers, allow_redirects=True, timeout=30)
                current_html = auth_resp.text
                current_url = auth_resp.url
                print(get_text("form_submitted", LANGUAGE))

        if DEBUG:
            html_path = DEBUG_DIR / "jobpol_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(current_html)

        print(get_text("extracting_jobs", LANGUAGE))

        page_index = 1
        max_pages = 25

        while page_index <= max_pages:
            page_soup = BeautifulSoup(current_html, "html.parser")
            tiles = page_soup.select(".tile--vacancy-overview, .views-row .tile")

            for tile in tiles:
                link_elem = tile.select_one("a.tile__inner") or tile.select_one("a")
                href = link_elem.get("href", "") if link_elem else ""
                url = urljoin(JOBPOL_URL, href)

                title_elem = tile.select_one(".tile__title__inner") or tile.select_one(".tile__title")
                title = title_elem.get_text(strip=True) if title_elem else "Poste Jobpol"

                loc_elem = tile.select_one(".tile__title--zip")
                zone = loc_elem.get_text(strip=True) if loc_elem else ""

                date_elem = tile.select_one(".tile__title--register_date") or tile.select_one(".tile__title--register")
                deadline = date_elem.get_text(strip=True) if date_elem else ""

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

            next_link = page_soup.select_one(".pager__item--next a") or page_soup.select_one("a[rel='next']")
            if next_link and next_link.get("href"):
                next_url = urljoin(current_url, next_link.get("href"))
                page_index += 1
                next_resp = session.get(next_url, timeout=30)
                current_html = next_resp.text
                current_url = next_resp.url
            else:
                break

        print(get_text("jobs_found", LANGUAGE, count=len(jobs)))

    except Exception as e:
        print(get_text("unexpected_error", LANGUAGE, error=e))

    return jobs
