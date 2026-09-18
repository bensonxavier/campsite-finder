def test_app_import():
    # Skip this test if streamlit is not installed in the test environment.
    import pytest
    pytest.importorskip("streamlit")
    # importing app should not raise at module import time
    import importlib
    importlib.import_module('app')
    import app
    from campsite_finder import utils

    # ensure pandas is imported in the app module to avoid runtime NameError
    assert hasattr(app, "pd")
    assert app.find_reservation_url is utils.find_reservation_url

    fumotoppara = next(site for site in app.CAMPSITES if site["name"] == "Fumotoppara")
    assert fumotoppara["reservation_url"] == "https://fumotoppara.net/en/reservation/"

    fujiyoshida = next(site for site in app.CAMPSITES if site["name"] == "PICA Fujiyoshida")
    assert fujiyoshida["reservation_url"] == "https://booking.pica-resort.jp/v3/calendar/stay/1"

    grinpa = next(site for site in app.CAMPSITES if site["name"] == "PICA Fuji Grinpa")
    assert grinpa["reservation_url"] == "https://booking.pica-resort.jp/v3/calendar/stay/3"

    nasu = next(site for site in app.CAMPSITES if site["name"] == "CAMP AND CABINS Nasu Kogen")
    assert nasu["reservation_url"] == "https://reser.camp-cabins.com/cc_reserve/sv_open"

    ogose = next(site for site in app.CAMPSITES if site["name"] == "BIO-RESORT HOTEL & SPA OPARK Ogose")
    assert ogose["reservation_url"] == "https://go-onsendojo.reservation.jp/ja/hotels/opark/searchInput"
