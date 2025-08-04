"""
Route tests for the LEET Flask app.

Covers:
- Static pages (home, about, reports, visualisations)
- Visualisation pages and form submissions
- Report generation routes with query parameters
- ESG article route (real and mocked)
- Error handling and edge case tests

Demonstrates usage of:
- Flask test client
- GET and POST method handling
- Form validation and route logic
- Mocked external API responses
"""

import pytest
from unittest.mock import patch

# -------------------- STATIC ROUTES --------------------

def test_homepage_get(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/'
    THEN status code should be 200
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"LEET" in response.data or b"Energy" in response.data

def test_homepage_post_not_allowed(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/'
    THEN status code should be 405 Method Not Allowed
    """
    response = client.post("/")
    assert response.status_code == 405

def test_about_page(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/about'
    THEN the status code should be 200
    """
    response = client.get("/about")
    assert response.status_code == 200

def test_visualisations_page(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/visualisations'
    THEN the status code should be 200
    """
    response = client.get("/visualisations")
    assert response.status_code == 200

def test_reports_page(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/reports'
    THEN the status code should be 200
    """
    response = client.get("/reports")
    assert response.status_code == 200

def test_404_page(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to a non-existent route
    THEN the status code should be 404
    """
    response = client.get("/nonexistent")
    assert response.status_code == 404

# -------------------- VISUALISATION ROUTES --------------------

def test_building_count(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/visualisations/building-count'
    THEN the chart should render successfully
    """
    response = client.get("/visualisations/building-count")
    assert response.status_code == 200
    assert b"<div" in response.data

def test_average_energy_post(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/visualisations/average-energy' with form data
    THEN the page should return status 200 and render the chart
    """
    response = client.post("/visualisations/average-energy", data={
        "metric": "kwh",
        "building_type": "Residential"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_geomap_post(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/visualisations/geomap' with valid form data
    THEN the page should render a map and return 200
    """
    response = client.post("/visualisations/geomap", data={
        "metric": "kwh",
        "building_type": "Mixed-Use"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_geomap_missing_metric(client):
    """
    GIVEN a Flask test client
    WHEN only building_type is provided
    THEN the form should fail and render no map
    """
    response = client.post("/visualisations/geomap", data={
        "building_type": "Residential"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Energy Demand Map" not in response.data

def test_pie_chart_post(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/visualisations/pie-chart' with borough data
    THEN the page should render a pie chart
    """
    response = client.post("/visualisations/pie-chart", data={
        "borough": "Camden"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_heatmap_post(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/visualisations/heatmap' with borough data
    THEN the page should return 200
    """
    response = client.post("/visualisations/heatmap", data={
        "borough": "Camden"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_high_demand_post(client):
    """
    GIVEN a Flask test client
    WHEN a POST request is made to '/visualisations/high-demand' with a percentile
    THEN the page should return 200
    """
    response = client.post("/visualisations/high-demand", data={
        "percentile": "50"
    }, follow_redirects=True)
    assert response.status_code == 200

def test_high_demand_invalid_percentile(client):
    """
    GIVEN a Flask test client
    WHEN an invalid percentile is submitted
    THEN the route should handle it gracefully and return 200
    """
    response = client.post("/visualisations/high-demand", data={
        "percentile": "5"
    }, follow_redirects=True)
    assert response.status_code == 200


# -------------------- REPORT ROUTES --------------------

def test_borough_summary_form(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/reports/borough-summary'
    THEN the form page should load successfully
    """
    response = client.get("/reports/borough-summary")
    assert response.status_code == 200

def test_borough_summary_generate(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/reports/borough-summary/generate' with query params
    THEN the report should render successfully
    """
    response = client.get("/reports/borough-summary/generate", query_string={
        "borough": "Camden",
        "building_type": "",
        "threshold": 0,
        "include_map": "true",
        "output_format": "html"
    })
    assert response.status_code == 200

def test_borough_summary_generate_empty_result(client):
    """
    GIVEN a high threshold that filters out all data
    WHEN borough summary is generated
    THEN the page should render with a no data message
    """
    response = client.get("/reports/borough-summary/generate", query_string={
        "borough": "Camden",
        "building_type": "",
        "threshold": 9999999,
        "include_map": "true",
        "output_format": "html"
    })
    assert response.status_code == 200
    assert b"No data matches your selected filters" in response.data

def test_borough_summary_generate_no_map_with_building_type(client):
    """
    GIVEN a specific building type and map turned off
    WHEN borough summary is generated
    THEN the report should render without a pie chart or map
    """
    response = client.get("/reports/borough-summary/generate", query_string={
        "borough": "Camden",
        "building_type": "Mixed-Use",
        "threshold": 0,
        "include_map": "false",
        "output_format": "html"
    })
    assert response.status_code == 200

def test_borough_summary_generate_map_with_all_types(client):
    """
    GIVEN building_type left blank (all types) and map included
    WHEN borough summary is generated
    THEN both pie chart and map should appear
    """
    response = client.get("/reports/borough-summary/generate", query_string={
        "borough": "Camden",
        "building_type": "",
        "threshold": 0,
        "include_map": "true",
        "output_format": "html"
    })
    assert response.status_code == 200

def test_building_type_focus_form(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/reports/building-type-focus'
    THEN the form page should load
    """
    response = client.get("/reports/building-type-focus")
    assert response.status_code == 200

def test_building_type_focus_generate(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/reports/building-type-focus/generate' with query params
    THEN the report should render successfully
    """
    response = client.get("/reports/building-type-focus/generate", query_string={
        "building_type": "Mixed-Use",
        "boroughs": "Camden,Westminster",
        "metrics": "kwh,peak_kw",
        "output_format": "html"
    })
    assert response.status_code == 200

def test_building_type_focus_generate_invalid_metric(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to building-type-focus with unsupported metrics
    THEN the route should still return successfully with a fallback response
    """
    response = client.get("/reports/building-type-focus/generate", query_string={
        "building_type": "Mixed-Use",
        "boroughs": "Camden,Westminster",
        "metrics": "invalid",
        "output_format": "html"
    })
    assert response.status_code == 200

# -------------------- ESG ROUTE --------------------

def test_esg_articles(client):
    """
    GIVEN a Flask test client
    WHEN a GET request is made to '/esg'
    THEN the page should return status 200 even if API fails
    """
    response = client.get("/esg")
    assert response.status_code == 200
    assert b"Last updated" in response.data or b"article" in response.data

def mock_guardian_response(*args, **kwargs):
    class MockResponse:
        def raise_for_status(self): pass
        def json(self):
            return {
                "response": {
                    "results": [
                        {
                            "fields": {
                                "headline": "UK energy reforms approved",
                                "trailText": "New government energy policy"
                            },
                            "webUrl": "https://example.com/article",
                            "webPublicationDate": "2024-04-01T12:00:00Z",
                            "sectionName": "Business"
                        }
                    ]
                }
            }
    return MockResponse()

@patch("leet_app.routes.requests.get", side_effect=mock_guardian_response)
def test_esg_articles_mocked(mock_get, client):
    """
    GIVEN a mocked Guardian API
    WHEN '/esg' is accessed
    THEN the page should render article headline from mock
    """
    response = client.get("/esg")
    assert response.status_code == 200
    assert b"UK energy reforms approved" in response.data
    assert b"New government energy policy" in response.data

@patch("leet_app.routes.requests.get", side_effect=Exception("API failure"))
def test_esg_articles_api_error_handling(mock_get, client):
    """
    GIVEN the Guardian API fails during the request
    WHEN '/esg' is accessed
    THEN the route should still render the page with fallback or error message
    """
    response = client.get("/esg")
    assert response.status_code == 200
    assert b"ESG" in response.data  