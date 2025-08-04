"""
Forms for LEET Visualisation Filters.

This module defines Flask-WTF forms used in the LEET app to filter energy usage data
and generate charts for various visualisations. Forms include selection for building type,
boroughs, energy metrics, and thresholds.

Dependencies:
    - Flask-WTF
    - WTForms
"""

from wtforms import (
    BooleanField,
    SelectField,
    SelectMultipleField,
    SubmitField,
    RadioField,
    DecimalField,
    widgets,
)
from wtforms.validators import DataRequired, Optional, NumberRange, ValidationError
from flask_wtf import FlaskForm


class AverageEnergyForm(FlaskForm):
    """
    Form to filter data for the average energy chart by metric and building type.
    """

    metric = SelectField(
        label="Energy Metric",
        choices=[("kwh", "kWh"), ("peak_kw", "Peak kW")],
        validators=[DataRequired()],
    )
    building_type = SelectField(
        label="Building Type",
        choices=[],  # dynamically populated in the route
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate Chart")


class GeomapFilterForm(FlaskForm):
    """
    Form for selecting filters to generate a geospatial energy demand map.
    """

    metric = SelectField(
        label="Energy Metric",
        choices=[("kwh", "kWh"), ("peak_kw", "Peak kW")],
        validators=[DataRequired()],
    )
    building_type = SelectField(
        label="Building Type",
        choices=[],  # dynamically populated
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate Map")


class PieChartFilterForm(FlaskForm):
    """
    Form to select a borough for generating a pie chart of energy distribution.
    """

    borough = SelectField(
        label="Borough",
        choices=[],  # dynamically populated
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate Pie Chart")


class HeatmapForm(FlaskForm):
    """
    Form to select a borough for displaying the energy density heatmap.
    """

    borough = SelectField(
        label="Borough",
        choices=[],  # dynamically populated
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate Heatmap")


class HighDemandForm(FlaskForm):
    """
    Form to select a KWH percentile threshold for identifying high-demand buildings.
    """

    percentile = SelectField(
        label="KWH Percentile Threshold",
        choices=[
            ("50", "Top 50%"),
            ("75", "Top 25%"),
            ("90", "Top 10%"),
            ("95", "Top 5%"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Generate Chart")


class BoroughReportForm(FlaskForm):
    """
    Form for generating a report filtered by borough, building type, threshold, and output format.
    """
    borough = SelectField(
        "Borough",
        validators=[DataRequired()],
        choices=[],  # Populated dynamically in route
    )

    building_type = SelectField(
        "Building Type",
        validators=[Optional()],
        choices=[],  # Populated dynamically in route
    )

    threshold = DecimalField(
        "Minimum kWh Threshold",
        validators=[Optional(), NumberRange(min=0)],
        places=0,
        default=0,
    )

    include_map = BooleanField("Include Geomap in Report")

    output_format = RadioField(
        "Output Format",
        choices=[("html", "HTML"), ("csv", "CSV")],
        default="html",
        validators=[DataRequired()],
    )

    submit = SubmitField("Generate Report")


class BuildingTypeReportForm(FlaskForm):
    """
    Form for generating a report filtered by building type, energy metrics, 
    boroughs, and output format.
    """
    building_type = SelectField(
        "Building Type",
        choices=[],  # populated dynamically
        validators=[DataRequired()],
    )

    metrics = SelectMultipleField(
        "Select Energy Metrics",
        choices=[("kwh", "Annual Energy Use (kWh)"), ("peak_kw", "Peak Demand (kW)")],
        validators=[],  # Custom validation below
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )

    boroughs = SelectMultipleField(
        "Select Boroughs",
        choices=[],  # populated dynamically
        validators=[],  # Custom validation below
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
    )

    output_format = RadioField(
        "Output Format",
        choices=[("html", "HTML"), ("csv", "CSV")],
        default="html",
        validators=[DataRequired()],
    )

    submit = SubmitField("Generate Report")

    # Custom validations
    def validate_metrics(self, field):
        """
        Validates that at least one energy metric is selected.
        """
        if not self.metrics.data:
            raise ValidationError("Please select at least one metric.")

    def validate_boroughs(self, field):
        """
        Validates that at least one borough is selected.
        """
        if not self.boroughs.data:
            raise ValidationError("Please select at least one borough.")
        