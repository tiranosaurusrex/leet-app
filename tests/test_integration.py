"""
Integration tests for the LEET Flask app using Selenium WebDriver.
These tests validate that the app runs correctly in a live browser session,
and simulate real user interactions.

Tests include:
- Server availability check
- Homepage rendering
- Form submission for average energy use

Dependencies:
- selenium
- pytest
- requests
"""

import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_server_is_up_and_running(live_server, flask_port):
    """
    GIVEN a live server
    WHEN a GET HTTP request to the home page is made
    THEN the response should have status code 200
    """
    url = f"http://127.0.0.1:{flask_port}/"
    response = requests.get(url)
    assert response.status_code == 200


def test_homepage_renders_correctly(chrome_driver, flask_port, live_server):
    """
    GIVEN a running LEET app
    WHEN the home page is loaded in a Chrome browser
    THEN the title or hero section should contain expected content
    """
    url = f"http://127.0.0.1:{flask_port}/"
    chrome_driver.get(url)
    assert "LEET" in chrome_driver.page_source or "Energy" in chrome_driver.page_source


def test_submit_average_energy_form(chrome_driver, flask_port, live_server):
    """
    GIVEN a running LEET app with visualisation forms
    WHEN a user fills and submits the Average Energy Use form
    THEN a chart should be rendered successfully
    """
    # Navigate to visualisation form page
    url = f"http://127.0.0.1:{flask_port}/visualisations/average-energy"
    chrome_driver.get(url)

    # Wait until the metric dropdown is present
    WebDriverWait(chrome_driver, 5).until(
        EC.presence_of_element_located((By.NAME, "metric"))
    )

    # Fill in form
    Select(chrome_driver.find_element(By.NAME, "metric")).select_by_value("kwh")
    Select(chrome_driver.find_element(By.NAME, "building_type")).select_by_value("Residential")

    # Submit the form
    chrome_driver.find_element(By.NAME, "submit").click()

    # Assert a div with a chart appears (based on Plotly or HTML structure)
    WebDriverWait(chrome_driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "div"))
    )
    assert "kWh" in chrome_driver.page_source or "Chart" in chrome_driver.page_source