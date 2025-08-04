# Copied from Flask documentation: https://flask.palletsprojects.com/en/stable/testing/
import os
import pytest
import socket
import subprocess
import time
from selenium.webdriver import Chrome, ChromeOptions
from leet_app import create_app, db


@pytest.fixture(scope="module")
def app():
    """
    Create and configure a Flask app for testing with an in-memory DB.
    No mock data is inserted. Each test can insert its own data if needed.
    """
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="module")
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture(scope="module")
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture(scope="module")
def chrome_driver():
    """Creates a Chrome driver with headless support for CI environments."""
    options = ChromeOptions()
    if "GITHUB_ACTIONS" in os.environ:
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
    else:
        options.add_argument("start-maximized")
    driver = Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def flask_port():
    """Get a free port from the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(flask_port):
    """Run the Flask app as a live server for Selenium tests."""
    os.environ["FLASK_APP"] = "leet_app:create_app"
    os.environ["FLASK_RUN_PORT"] = str(flask_port)
    os.environ["FLASK_ENV"] = "development" 

    command = "flask run"
    server = subprocess.Popen(command, shell=True)

    time.sleep(3)  # wait for server to boot
    yield server
    server.terminate()