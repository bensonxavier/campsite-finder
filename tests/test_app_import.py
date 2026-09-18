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
