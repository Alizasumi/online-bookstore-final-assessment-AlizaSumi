import os
import sys
import pytest
from importlib import import_module

@pytest.fixture(scope="session")
def app():
    """Import the Flask app from app.py and configure testing mode."""
    sys.path.insert(0, os.getcwd())
    app_module = import_module("app")
    flask_app = getattr(app_module, "app", None)
    if flask_app is None and hasattr(app_module, "create_app"):
        flask_app = app_module.create_app(testing=True)
    if flask_app is None:
        raise RuntimeError("No Flask app found in app.py")
    flask_app.config.update(TESTING=True, SERVER_NAME="localhost")
    return flask_app

@pytest.fixture()
def client(app):
    return app.test_client()