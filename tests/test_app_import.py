def test_app_import():
    # importing app should not raise at module import time
    import importlib
    importlib.import_module('app')
