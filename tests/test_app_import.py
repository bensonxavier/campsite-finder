def test_app_import():
    # Skip this test if streamlit is not installed in the test environment.
    import pytest
    pytest.importorskip("streamlit")
    # importing app should not raise at module import time
    import importlib
    importlib.import_module('app')
