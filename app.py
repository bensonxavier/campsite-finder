import streamlit as st
import pandas as pd
from datetime import date, timedelta
from campsite_finder.utils import (
    simulate_availability,
    color_for_status,
    find_reservation_url,
    is_jp_holiday,
)


st.set_page_config(page_title="Family Campsite Availability Finder", layout="wide")


CAMPSITES = [
    {
        "name": "PICA Fuji Grinpa",
        "region": "Mt. Fuji",
        "activities": ["Kids playground", "Splash area", "Forest trails"],
        "url": "https://pica-resort.jp/en/fuji_grinpa/",
        "reservation_url": "https://pica-resort.jp/en/fuji_grinpa/",
        "types": ["Cabin / Cottage", "Tent Site", "Glamping / Dome"],
    },
    {
        "name": "PICA Fujiyoshida",
        "region": "Mt. Fuji",
        "activities": ["Lake views", "Kids workshop", "BBQ area"],
        "url": "https://pica-resort.jp/en/fujiyoshida/",
        "reservation_url": "https://pica-resort.jp/en/fujiyoshida/",
        "types": ["Cabin / Cottage", "Tent Site"],
    },
    {
        "name": "Fumotoppara",
        "region": "Mt. Fuji",
        "activities": ["Open grass fields", "Stargazing", "Kids playground"],
        "url": "https://fumotoppara.net/en/",
        "reservation_url": "https://fumotoppara.net/en/reservation/",
        "types": ["Tent Site", "Glamping / Dome"],
    },
    {
        "name": "BIO-RESORT HOTEL & SPA OPARK Ogose",
        "region": "Saitama",
        "activities": ["Amusement park", "Children's pool", "Nature trails"],
        "url": "https://www.opark.co.jp/ogose/",
        "reservation_url": "https://www.opark.co.jp/ogose/",
        "types": ["Cabin / Cottage", "Tent Site"],
    },
    {
        "name": "CAMP AND CABINS Nasu Kogen",
        "region": "Nasu Kogen",
        "activities": ["Tree hammocks", "Play area", "Campfire program"],
        "url": "https://nasukogen.camp/",
        "reservation_url": "https://nasukogen.camp/",
        "types": ["Cabin / Cottage", "Glamping / Dome"],
    },
]



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
