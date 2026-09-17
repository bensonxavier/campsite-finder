import hashlib
import datetime
from datetime import date, timedelta
from typing import List, Dict

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="Family Campsite Availability Finder", layout="wide")


CAMPSITES = [
    {
        "name": "PICA Fuji Grinpa",
        "region": "Mt. Fuji",
        "activities": ["Kids playground", "Splash area", "Forest trails"],
        "url": "https://pica-resort.jp/en/fuji_grinpa/",
        "types": ["Cabin / Cottage", "Tent Site", "Glamping / Dome"],
    },
    {
        "name": "PICA Fujiyoshida",
        "region": "Mt. Fuji",
        "activities": ["Lake views", "Kids workshop", "BBQ area"],
        "url": "https://pica-resort.jp/en/fujiyoshida/",
        "types": ["Cabin / Cottage", "Tent Site"],
    },
    {
        "name": "Fumotoppara",
        "region": "Mt. Fuji",
        "activities": ["Open grass fields", "Stargazing", "Kids playground"],
        "url": "https://www.fumotoppara.co.jp/",
        "types": ["Tent Site", "Glamping / Dome"],
    },
    {
        "name": "BIO-RESORT HOTEL & SPA OPARK Ogose",
        "region": "Saitama",
        "activities": ["Amusement park", "Children's pool", "Nature trails"],
        "url": "https://www.opark.co.jp/ogose/",
        "types": ["Cabin / Cottage", "Tent Site"],
    },
    {
        "name": "CAMP AND CABINS Nasu Kogen",
        "region": "Nasu Kogen",
        "activities": ["Tree hammocks", "Play area", "Campfire program"],
        "url": "https://nasukogen.camp/",
        "types": ["Cabin / Cottage", "Glamping / Dome"],
    },
]


JP_HOLIDAYS: Dict[str, str] = {
    # Example set — extend as needed. Format: YYYY-MM-DD: "Holiday Name"
    "2026-01-01": "New Year's Day",
    "2026-02-11": "National Foundation Day",
    "2026-04-29": "Showa Day",
    "2026-05-03": "Constitution Memorial Day",
    "2026-05-04": "Greenery Day",
    "2026-05-05": "Children's Day",
    "2026-09-23": "Autumnal Equinox Day",
    "2026-11-03": "Culture Day",
    "2026-11-23": "Labor Thanksgiving Day",
    "2026-10-??": "Sports Day (variable)",
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
            # deterministic thresholds: 0-9 Full, 10-29 Few Left, 30-99 Available
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


def main():
    st.title("Family Campsite Availability Finder — Japan")

    # Sidebar filters
    st.sidebar.header("Filters")
    regions = list(sorted({c["region"] for c in CAMPSITES}))
    selected_regions = st.sidebar.multiselect("Regions", regions, default=regions)

    acc_types = ["Cabin / Cottage", "Tent Site", "Glamping / Dome"]
    selected_types = st.sidebar.multiselect("Accommodation types", acc_types, default=acc_types)

    horizon_map = {"Next 30 Days": 30, "Next 60 Days": 60, "Next 90 Days": 90}
    horizon_label = st.sidebar.radio("Search horizon", list(horizon_map.keys()), index=0)
    days = horizon_map[horizon_label]

    st.sidebar.markdown("---")
    st.sidebar.subheader("Priority Day Selector")
    weekends = st.sidebar.checkbox("Weekends (Sat/Sun)", value=False)
    holidays = st.sidebar.checkbox("Japanese National Holidays", value=False)

    weekdays_defaults = {"Mon": False, "Tue": False, "Wed": False, "Thu": False, "Fri": True}
    selected_weekdays = {}
    cols = st.sidebar.columns(1)
    for wd in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        selected_weekdays[wd] = st.sidebar.checkbox(wd, value=weekdays_defaults[wd])

    include_full = st.sidebar.checkbox("Include fully booked dates (🔴 Full)", value=False)

    # compute date range
    today = date.today()
    start = today
    end = today + timedelta(days=days)

    # helper to check whether a date matches the priority selections
    def date_matches(d: date) -> bool:
        weekday_name = d.strftime("%a")  # Mon, Tue, ...
        is_weekend = d.weekday() >= 5
        is_hol = is_jp_holiday(d)

        matches = False
        if weekends and is_weekend:
            matches = True
        if holidays and is_hol:
            matches = True
        # weekday toggles
        if weekday_name in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            short = weekday_name[:3]
            if selected_weekdays.get(short, False) and not is_weekend:
                matches = True

        # If user didn't select any of weekend/holiday/weekday options, treat it as "no restriction"
        any_selected = weekends or holidays or any(selected_weekdays.values())
        return matches if any_selected else True

    st.sidebar.markdown("---")
    st.sidebar.write(f"Searching {start.isoformat()} → {end.isoformat()} ({days} days)")

    # build filtered campsite list
    filtered_sites = [c for c in CAMPSITES if c["region"] in selected_regions and any(t in c["types"] for t in selected_types)]

    if not filtered_sites:
        st.warning("No campsites match the selected region/accommodation filters.")
        return

    # Main layout: grouped by campsite
    for site in filtered_sites:
        # determine best reservation link by probing common paths
        import re
        from urllib.parse import urljoin

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
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
            # find href attributes and return absolute URLs containing booking keywords
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
            keywords = ["reserve", "reservation", "booking", "book", "reserve_", "reserva"]
            results = []
            for h in hrefs:
                low = h.lower()
                if any(k in low for k in keywords):
                    # make absolute
                    results.append(urljoin(base, h))
            return results

        def find_reservation_url(site: dict) -> str:
            base = site.get("url")

            # quick candidates (common paths)
            common = [
                base,
                base.rstrip("/") + "/reserve",
                base.rstrip("/") + "/reservation",
                base.rstrip("/") + "/reserva",
                base.rstrip("/") + "/en/reserve",
                base.rstrip("/") + "/reserve/",
                base.rstrip("/") + "/booking",
            ]

            # try common candidates first
            for c in common:
                if validate_url(c):
                    return c

            # fetch base page and search for booking links
            try:
                resp = requests.get(base, allow_redirects=True, timeout=8, headers=HEADERS)
                if resp.status_code < 400 and resp.text:
                    candidates = _extract_candidate_links(resp.text, base)
                    for c in candidates:
                        if validate_url(c):
                            return c
            except Exception:
                pass

            # fallback: return base URL (may be the only entry point)
            return base

        reservation_link = find_reservation_url(site)

        with st.expander(site["name"], expanded=False):
            left, right = st.columns([1, 2])
            with left:
                st.markdown(f"**Region:** {site['region']}")
                st.markdown("**Activities:**")
                for a in site["activities"]:
                    st.markdown(f"- {a}")
                label = "Reservation page" if reservation_link != site.get("url") else "Official page"
                st.markdown(f'<a href="{reservation_link}" target="_blank">{label}</a>', unsafe_allow_html=True)
                # If we couldn't find a distinct reservation page, offer a search link to help users locate booking
                if reservation_link == site.get("url"):
                    import urllib.parse

                    q = urllib.parse.quote_plus(f"{site['name']} reservation booking")
                    search_url = f"https://www.google.com/search?q={q}"
                    st.markdown(f'<a href="{search_url}" target="_blank">Search for reservation page</a>', unsafe_allow_html=True)

            with right:
                df = simulate_availability(site["name"], start, end, [t for t in selected_types if t in site["types"]])
                # filter date types by priority
                df = df[df["Date"].apply(date_matches)]
                if not include_full:
                    df = df[~df["Status"].str.startswith("🔴")]

                if df.empty:
                    st.info("No available slots found for the selected filters and date range.")
                else:
                    # present a clean table
                    df_display = df.copy()
                    # ensure Date column is datetimelike before using .dt
                    df_display["Date"] = pd.to_datetime(df_display["Date"])
                    df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d (%a)")
                    df_display = df_display.sort_values(["Date", "Type"])
                    styled = df_display.style.applymap(color_for_status, subset=["Status"])  # type: ignore
                    st.dataframe(styled, use_container_width=True)


if __name__ == "__main__":
    main()
