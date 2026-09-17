def test_app_import():
    # Skip this test if streamlit is not installed in the test environment.
    import pytest
    pytest.importorskip("streamlit")
    # importing app should not raise at module import time
    import importlib
    importlib.import_module('app')
    import app
    # ensure pandas is imported in the app module to avoid runtime NameError
    assert hasattr(app, "pd")
