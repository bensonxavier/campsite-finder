import hashlib
from datetime import date, timedelta
from typing import List, Dict

import pandas as pd
import requests


JP_HOLIDAYS: Dict[str, str] = {
    "2026-01-01": "New Year's Day",
    "2026-02-11": "National Foundation Day",
    "2026-04-29": "Showa Day",
    "2026-05-03": "Constitution Memorial Day",
    "2026-05-04": "Greenery Day",
    "2026-05-05": "Children's Day",
    "2026-09-23": "Autumnal Equinox Day",
    "2026-11-03": "Culture Day",
    "2026-11-23": "Labor Thanksgiving Day",
}


def is_jp_holiday(d: date) -> bool:
    return d.isoformat() in JP_HOLIDAYS


def md5_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)


def simulate_availability(site_name: str, start: date, end: date, types: List[str]) -> pd.DataFrame:
    rows = []
    delta = (end - start).days
    for i in range(delta + 1):
        d = start + timedelta(days=i)
        for t in types:
            seed = f"{site_name}|{d.isoformat()}|{t}"
            v = md5_int(seed) % 100
            if v < 10:
                status = "🔴 Full"
            elif v < 30:
                status = "🟡 Few Left"
            else:
                status = "🟢 Available"
            rows.append({"Date": d, "Type": t, "Status": status})
    df = pd.DataFrame(rows)
    return df


def color_for_status(val):
    if isinstance(val, str):
        if val.startswith("🟢"):
            return "background-color: #b7f5b7"
        if val.startswith("🟡"):
            return "background-color: #fff4b3"
        if val.startswith("🔴"):
            return "background-color: #f5b7b7"
    return ""


from urllib.parse import urljoin
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def validate_url(u: str) -> bool:
    try:
        resp = requests.head(u, allow_redirects=True, timeout=6, headers=HEADERS)
        if resp.status_code < 400:
            return True
    except Exception:
        pass
    try:
        resp = requests.get(u, allow_redirects=True, timeout=8, headers=HEADERS)
        return resp.status_code < 400
    except Exception:
        return False


def _extract_candidate_links(html: str, base: str):
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    keywords = ["reserve", "reservation", "booking", "book", "reserve_", "reserva", "yoyaku", "予約"]
    results = []
    for h in hrefs:
        low = h.lower()
        if any(k in low for k in keywords):
            results.append(urljoin(base, h))
    return results


def find_reservation_url(site: dict) -> str:
    explicit = site.get("reservation_url")
    if explicit and validate_url(explicit):
        return explicit

    base = site.get("url")
    common = [
        base,
        base.rstrip("/") + "/reserve",
        base.rstrip("/") + "/reservation",
        base.rstrip("/") + "/reserva",
        base.rstrip("/") + "/en/reserve",
        base.rstrip("/") + "/reserve/",
        base.rstrip("/") + "/booking",
    ]
    for c in common:
        if validate_url(c):
            return c

    try:
        resp = requests.get(base, allow_redirects=True, timeout=8, headers=HEADERS)
        if resp.status_code < 400 and resp.text:
            candidates = _extract_candidate_links(resp.text, base)
            for c in candidates:
                if validate_url(c):
                    return c
    except Exception:
        pass

    return base
