import hashlib
import sys
from urllib.parse import urljoin
from typing import List, Dict, Any, Tuple

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
    FILTER_UNIT,
    FILTER_GRADE,
    FILTER_REGION,
)
from translations import get_text


UNIT_MAP = {
    "LOCAL": "0",
    "LOCALE": "0",
    "POLICE_LOCALE": "0",
    "POLICE_LOCAL": "0",
    "0": "0",
    "FEDERAL": "1",
    "FEDERALE": "1",
    "POLICE_FEDERALE": "1",
    "POLICE_FEDERAL": "1",
    "1": "1",
}

GRADE_MAP = {
    "AGENT": "4892",
    "AGENT_POLICE": "4892",
    "AGENT_DE_POLICE": "4892",
    "SECURISATION": "4988",
    "AGENT_SECURISATION": "4988",
    "AGENT_DE_SECURISATION": "4988",
    "INSPECTEUR": "4895",
    "INSPECTEUR_POLICE": "4895",
    "INSPECTEUR_DE_POLICE": "4895",
    "COMMISSAIRE": "4901",
    "ECOFIN": "5006",
    "INPP_ECOFIN": "5006",
    "ICT": "5003",
    "INPP_ICT": "5003",
    "ASSISTANT": "5000",
    "ASSISTANT_POLICE": "5000",
    "LABO": "5012",
    "INPP_LABO": "5012",
    "ISLAMOLOGUE": "5009",
    "INPP_ISLAMOLOGUE": "5009",
}

REGION_MAP = {
    "ANVERS": "3265",
    "ANTWERPEN": "3265",
    "BRABANT_FLAMAND": "3275",
    "VLAAMS_BRABANT": "3275",
    "BRABANT_WALLON": "3274",
    "WAALS_BRABANT": "3274",
    "BRUXELLES": "3266",
    "BRUSSEL": "3266",
    "BRUXELLES_CAPITALE": "3266",
    "FLANDRE_OCCIDENTALE": "3267",
    "WEST_VLAANDEREN": "3267",
    "FLANDRE_ORIENTALE": "3268",
    "OOST_VLAANDEREN": "3268",
    "HAINAUT": "3269",
    "HENEGOUWEN": "3269",
    "LIEGE": "3270",
    "LUIK": "3270",
    "LIMBOURG": "3271",
    "LIMBURG": "3271",
    "LUXEMBOURG": "3272",
    "LUXEMBURG": "3272",
    "NAMUR": "3273",
    "NAMEN": "3273",
    "INTERNATIONAL": "_abroad",
    "ABROAD": "_abroad",
}


def build_filter_params(unit: str, grade: str, region: str) -> List[Tuple[str, str]]:
    params: List[Tuple[str, str]] = []
    if unit:
        u_items = [u.strip().upper() for u in unit.split(",") if u.strip()]
        for idx, item in enumerate(u_items):
            val = UNIT_MAP.get(item, item if item in ("0", "1") else None)
            if val:
                params.append((f"unit[{idx}]", val))
    if grade:
        g_items = [g.strip().upper() for g in grade.split(",") if g.strip()]
        for idx, item in enumerate(g_items):
            val = GRADE_MAP.get(item, item if item.isdigit() else None)
            if val:
                params.append((f"diploma[{idx}]", val))
    if region:
        r_items = [r.strip().upper() for r in region.split(",") if r.strip()]
        for idx, item in enumerate(r_items):
            val = REGION_MAP.get(item, item if (item.isdigit() or item == "_abroad") else None)
            if val:
                params.append((f"region[{idx}]", val))
    return params


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

        filter_params = build_filter_params(FILTER_UNIT, FILTER_GRADE, FILTER_REGION)
        if filter_params:
            print(
                get_text(
                    "filters_applied",
                    LANGUAGE,
                    unit=FILTER_UNIT or "ALL",
                    grade=FILTER_GRADE or "ALL",
                    region=FILTER_REGION or "ALL",
                )
            )
            filtered_resp = session.get(
                JOBPOL_URL,
                params=filter_params,
                headers={"Referer": current_url},
                timeout=30,
            )
            if filtered_resp.status_code == 200:
                current_html = filtered_resp.text
                current_url = filtered_resp.url

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
