"""
Unit tests for Flask-WTF forms used in the LEET app.
Covers validation logic, default values, and edge cases.
"""

import pytest
from wtforms.validators import ValidationError
from leet_app.forms import (
    AverageEnergyForm,
    GeomapFilterForm,
    PieChartFilterForm,
    HeatmapForm,
    HighDemandForm,
    BoroughReportForm,
    BuildingTypeReportForm,
)

def test_average_energy_form_valid(app):
    """
    GIVEN an AverageEnergyForm
    WHEN valid metric and building_type are provided
    THEN the form should validate successfully
    """
    with app.test_request_context():
        form = AverageEnergyForm(data={"metric": "kwh", "building_type": "Residential"})
        form.building_type.choices = [("Residential", "Residential")]
        assert form.validate()


def test_geomap_filter_form_valid(app):
    """
    GIVEN a GeomapFilterForm
    WHEN valid metric and building_type are provided
    THEN the form should validate successfully
    """
    with app.test_request_context():
        form = GeomapFilterForm(data={"metric": "peak_kw", "building_type": "Non-Residential"})
        form.building_type.choices = [("Non-Residential", "Non-Residential")]
        assert form.validate()


def test_pie_chart_form_missing_borough(app):
    """
    GIVEN a PieChartFilterForm
    WHEN borough is missing
    THEN the form should fail validation
    """
    with app.test_request_context():
        form = PieChartFilterForm(data={"borough": ""})
        form.borough.choices = [("Camden", "Camden")]
        assert not form.validate()


def test_heatmap_form_valid(app):
    """
    GIVEN a HeatmapForm
    WHEN a valid borough is selected
    THEN the form should validate successfully
    """
    with app.test_request_context():
        form = HeatmapForm(data={"borough": "Westminster"})
        form.borough.choices = [("Westminster", "Westminster")]
        assert form.validate()


def test_high_demand_form_invalid_percentile(app):
    """
    GIVEN a HighDemandForm
    WHEN an invalid percentile not in choices is submitted
    THEN the form should fail validation
    """
    with app.test_request_context():
        form = HighDemandForm(data={"percentile": "10"})
        form.percentile.choices = [
            ("50", "Top 50%"),
            ("75", "Top 25%"),
            ("90", "Top 10%"),
            ("95", "Top 5%"),
        ]
        assert not form.validate()


def test_borough_report_form_negative_threshold(app):
    """
    GIVEN a BoroughReportForm
    WHEN a negative threshold is submitted
    THEN the form should fail validation due to NumberRange(min=0)
    """
    with app.test_request_context():
        form = BoroughReportForm()
        form.borough.choices = [("Camden", "Camden")]
        form.building_type.choices = [("Mixed-Use", "Mixed-Use")]

        form.process(data={
            "borough": "Camden",
            "building_type": "Mixed-Use",
            "threshold": "-10", 
            "include_map": True,
            "output_format": "html"
        })

        assert not form.validate()

def test_borough_report_form_valid(app):
    """
    GIVEN a BoroughReportForm
    WHEN all required fields are correctly filled
    THEN the form should validate successfully
    """
    with app.test_request_context():
        form = BoroughReportForm(
            data={
                "borough": "Camden",
                "building_type": "",
                "threshold": 0,
                "include_map": False,
                "output_format": "csv",
            }
        )
        form.borough.choices = [("Camden", "Camden")]
        form.building_type.choices = [("", "All")]
        assert form.validate()


def test_building_type_report_form_missing_metrics_and_boroughs(app):
    """
    GIVEN a BuildingTypeReportForm
    WHEN no metrics and no boroughs are selected
    THEN the custom validation functions should raise ValidationError
    """
    with app.test_request_context():
        form = BuildingTypeReportForm(
            data={
                "building_type": "Unknown",
                "metrics": [],
                "boroughs": [],
                "output_format": "html",
            }
        )
        form.building_type.choices = [("Unknown", "Unknown")]
        form.metrics.choices = [("kwh", "Annual Energy Use (kWh)"), ("peak_kw", "Peak Demand (kW)")]
        form.boroughs.choices = [("Camden", "Camden")]

        with pytest.raises(ValidationError):
            form.validate_metrics(form.metrics)
        with pytest.raises(ValidationError):
            form.validate_boroughs(form.boroughs)


def test_building_type_report_form_valid(app):
    """
    GIVEN a BuildingTypeReportForm
    WHEN all required fields including metrics and boroughs are selected
    THEN the form should validate successfully
    """
    with app.test_request_context():
        form = BuildingTypeReportForm(
            data={
                "building_type": "Residential",
                "metrics": ["kwh"],
                "boroughs": ["Camden"],
                "output_format": "csv",
            }
        )
        form.building_type.choices = [("Residential", "Residential")]
        form.metrics.choices = [("kwh", "Annual Energy Use (kWh)"), ("peak_kw", "Peak Demand (kW)")]
        form.boroughs.choices = [("Camden", "Camden")]
        assert form.validate()
