import datetime
from datetime import date, timedelta

import os
import sys
import pandas as pd
import pytest

# Ensure repo root is on sys.path for imports when running tests locally
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from campsite_finder import utils


def test_md5_int_deterministic():
    a = utils.md5_int("site|2026-01-01|Tent Site")
    b = utils.md5_int("site|2026-01-01|Tent Site")
    assert isinstance(a, int)
    assert a == b


def test_simulate_availability_structure():
    start = date(2026, 9, 1)
    end = date(2026, 9, 3)
    df = utils.simulate_availability("TestSite", start, end, ["Tent Site", "Cabin / Cottage"])
    assert isinstance(df, pd.DataFrame)
    # 3 days + inclusive -> 3 days * 2 types = 6 rows
    assert len(df) == 6
    assert set(df.columns) >= {"Date", "Type", "Status"}


def test_is_jp_holiday_true():
    assert utils.is_jp_holiday(date(2026, 1, 1))


def test_find_reservation_url_prefers_explicit(monkeypatch):
    site = {"url": "https://example.com/", "reservation_url": "https://example.com/book"}

    class DummyResp:
        def __init__(self, code=200):
            self.status_code = code

    def fake_head(u, allow_redirects=True, timeout=6, headers=None):
        if u == site["reservation_url"]:
            return DummyResp(200)
        return DummyResp(404)

    monkeypatch.setattr(utils.requests, "head", fake_head)

    chosen = utils.find_reservation_url(site)
    assert chosen == site["reservation_url"]


def test_find_reservation_url_scrapes_links(monkeypatch):
    site = {"url": "https://base.example/", "reservation_url": None}

    html = '<a href="/reserve">Reserve now</a>'

    class DummyResp:
        def __init__(self, code=200, text=None):
            self.status_code = code
            self.text = text

    def fake_head(u, allow_redirects=True, timeout=6, headers=None):
        # emulate head failing for common paths
        return DummyResp(404)

    def fake_get(u, allow_redirects=True, timeout=8, headers=None):
        if u == site["url"]:
            return DummyResp(200, text=html)
        if u.endswith("/reserve") or u.endswith("/reserve/"):
            return DummyResp(200, text="ok")
        return DummyResp(404)

    monkeypatch.setattr(utils.requests, "head", fake_head)
    monkeypatch.setattr(utils.requests, "get", fake_get)

    chosen = utils.find_reservation_url(site)
    assert chosen.endswith("/reserve") or chosen.endswith("/reserve/")
