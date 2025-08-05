"""
LEET Flask Routes Module.

This module defines all route handlers for the LEET app. It includes:

- Static page routes (home, about, contact, visualisations, reports)
- Visualisation routes for exploring energy data with Plotly
- Report generation routes for borough and building type summaries
- ESG news articles fetched from the Guardian API
- Integration with SQLAlchemy models and forms (Flask-WTF)
- Data retrieved via Flask-SQLAlchemy queries and rendered with Jinja templates

Each route uses a consistent structure:
    - Route + method
    - Optional Flask-WTF form handling
    - Optional SQLAlchemy query
    - Renders a Jinja template with a chart or table

Blueprint: 'starter'
"""

import os
from datetime import datetime

import requests
import pandas as pd
from dotenv import load_dotenv
from flask import Blueprint, render_template, request, redirect, url_for, Response

from src.leet_app.extensions import db
from src.leet_app.forms import (
    AverageEnergyForm,
    GeomapFilterForm,
    PieChartFilterForm,
    HeatmapForm,
    HighDemandForm,
    BoroughReportForm,
    BuildingTypeReportForm,
)
from src.leet_app.models import Borough, BuildingType, EnergyUsage
from src.leet_app.figures import (
    building_count_chart,
    create_avg_energy_chart,
    create_geomap_figure,
    generate_pie_chart_by_borough,
    create_energy_heatmap,
    create_high_demand_chart,
)
from src.leet_app.report_utils import (
    generate_borough_summary_data,
    generate_building_type_focus_data,
    create_report_geomap
)
load_dotenv()  # Load environment variables

bp = Blueprint("starter", __name__)  # Blueprint for main site routes

# -------------------- STATIC PAGES --------------------


@bp.route("/")
def index():
    """Render the home page."""
    return render_template("index.html")


@bp.route("/visualisations")
def visualisations():
    """Render the visualisations landing page."""
    return render_template("visualisations.html")


@bp.route("/reports")
def reports():
    """Render the reports page (to be implemented)."""
    return render_template("reports.html")

@bp.route("/about")
def about():
    """Render the about page."""
    return render_template("about.html")


# -------------------- VISUALISATION ROUTES --------------------

@bp.route("/visualisations/building-count")
def visualisation_building_count():
    """Show bar chart: number of buildings by borough and type."""
    chart_html = building_count_chart()["fig"]
    return render_template("visualisation_building_count.html", chart=chart_html)


@bp.route("/visualisations/average-energy", methods=["GET", "POST"])
def visualisation_average_energy():
    """Render average energy chart with filtering form."""
    form = AverageEnergyForm()
    form.building_type.choices = [
        (bt.building_type_name, bt.building_type_name)
        for bt in BuildingType.query.order_by(BuildingType.building_type_name).all()
    ]

    chart_html = None
    if form.validate_on_submit():
        metric = form.metric.data
        building_type = form.building_type.data
        chart_html = create_avg_energy_chart(metric, building_type)

    return render_template(
        "visualisation_avg_energy.html", form=form, chart_html=chart_html
    )


@bp.route("/visualisations/geomap", methods=["GET", "POST"])
def visualisation_geomap():
    """Render geomap based on selected energy metric and building type."""
    form = GeomapFilterForm()
    form.building_type.choices = [
        (bt.building_type_name, bt.building_type_name)
        for bt in db.session.execute(db.select(BuildingType)).scalars()
    ]

    chart_html = None
    if form.validate_on_submit():
        metric = form.metric.data
        building_type = form.building_type.data
        chart_html = create_geomap_figure(metric, building_type)

    return render_template("visualisation_geomap.html", form=form, chart=chart_html)


@bp.route("/visualisations/pie-chart", methods=["GET", "POST"])
def visualisation_pie_chart():
    """Render pie chart breaking down energy use by building type for a borough."""
    form = PieChartFilterForm()
    form.borough.choices = [
        (b.borough_name, b.borough_name)
        for b in db.session.scalars(db.select(Borough)).all()
    ]

    fig_html = None
    if form.validate_on_submit():
        fig = generate_pie_chart_by_borough(form.borough.data)
        fig_html = fig.to_html(full_html=False)

    return render_template("visualisation_pie_chart.html", form=form, fig_html=fig_html)


@bp.route("/visualisations/heatmap", methods=["GET", "POST"])
def visualisation_heatmap():
    """Render heatmap of energy demand across selected borough."""
    form = HeatmapForm()
    form.borough.choices = [
        (b.borough_name, b.borough_name)
        for b in Borough.query.order_by(Borough.borough_name).all()
    ]

    fig = None
    if form.validate_on_submit():
        selected_borough = form.borough.data
        fig = create_energy_heatmap(selected_borough)

    return render_template("visualisation_heatmap.html", form=form, fig=fig)


@bp.route("/visualisations/high-demand", methods=["GET", "POST"])
def visualisation_high_demand():
    """Render high energy demand bar chart using user-selected percentile."""
    form = HighDemandForm()
    fig = None
    threshold_kwh = None

    if form.validate_on_submit():
        percentile = int(form.percentile.data)
        stmt = db.select(EnergyUsage.kwh)
        df = pd.read_sql_query(stmt, db.engine)
        threshold_kwh = df["kwh"].quantile(percentile / 100)
        fig = create_high_demand_chart(threshold_kwh)

    return render_template(
        "visualisation_high_demand.html", form=form, fig=fig, threshold=threshold_kwh
    )

# -------------------- REPORT ROUTES --------------------
@bp.route("/reports/borough-summary", methods=["GET", "POST"])
def borough_summary_report():
    """ Renders the form to generate a borough summary report."""
    form = BoroughReportForm()

    # Populate dropdowns
    form.borough.choices = [
        (b.borough_name, b.borough_name)
        for b in Borough.query.order_by(Borough.borough_name).all()
    ]
    form.building_type.choices = [("", "All Types")] + [
        (bt.building_type_name, bt.building_type_name)
        for bt in BuildingType.query.all()
    ]

    if form.validate_on_submit():
        return redirect(
            url_for(
                "starter.borough_summary_generate",
                borough=form.borough.data,
                building_type=form.building_type.data,
                threshold=form.threshold.data or 0,
                include_map=form.include_map.data,
                output_format=form.output_format.data,
            )
        )

    return render_template("borough_summary_form.html", form=form)


@bp.route("/reports/borough-summary/generate")
def borough_summary_generate():
    """Generates a filtered borough summary report with optional charts and export options."""

    # --- Get parameters from query string ---
    borough = request.args.get("borough")
    building_type = request.args.get("building_type")
    threshold = request.args.get("threshold", type=float, default=0)
    include_map = request.args.get("include_map", "").lower() in [
        "true",
        "1",
        "yes",
        "on",
    ]
    output_format = request.args.get("output_format", default="html")

    # --- Retrieve processed data ---
    df, display_df, summary_stats, column_names, table_data = (
        generate_borough_summary_data(
            borough=borough, building_type=building_type, threshold=threshold
        )
    )

    if df is None:
        return render_template(
            "report_result.html",
            borough=borough,
            message="No data matches your selected filters.",
        )

    # --- Visuals ---
    fig_html = None
    if building_type == "":
        fig = generate_pie_chart_by_borough(borough)
        if fig:
            fig_html = fig.to_html(full_html=False)

    map_html = None
    if include_map:
        map_html = create_report_geomap(df, borough)

    # --- CSV Export ---
    if output_format == "csv":
        filename = f"Leet Borough Summary {borough.replace(' ', '_')}.csv"
        return Response(
            display_df.to_csv(index=False),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    # --- HTML Report View ---
    return render_template(
        "borough_summary_report.html",
        borough=borough,
        building_type=building_type or "All Types",
        threshold=threshold,
        include_map=include_map,
        table_data=table_data,
        column_names=column_names,
        fig_html=fig_html,
        map_html=map_html,
        total_buildings=summary_stats["total_buildings"],
        total_kwh=summary_stats["total_kwh"],
        avg_kwh=summary_stats["avg_kwh"],
        avg_peak_kw=summary_stats["avg_peak_kw"],
        now=datetime.now(),
    )


@bp.route("/reports/building-type-focus", methods=["GET", "POST"])
def building_type_focus_form():
    """Renders the form to generate a building type focus report."""
    form = BuildingTypeReportForm()

    # Populate dropdown choices dynamically
    form.building_type.choices = [
        (bt.building_type_name, bt.building_type_name)
        for bt in BuildingType.query.order_by(BuildingType.building_type_name).all()
    ]
    form.boroughs.choices = [
        (b.borough_name, b.borough_name)
        for b in Borough.query.order_by(Borough.borough_name).all()
    ]

    if form.validate_on_submit():
        return redirect(
            url_for(
                "starter.building_type_focus_report",
                building_type=form.building_type.data,
                boroughs=",".join(form.boroughs.data),
                metrics=",".join(form.metrics.data),
                output_format=form.output_format.data,
            )
        )

    return render_template("building_type_focus_form.html", form=form)


@bp.route("/reports/building-type-focus/generate")
def building_type_focus_report():
    """Generates a report comparing selected metrics across multiple boroughs 
    for a chosen building type."""

    # --- Get form parameters ---
    building_type = request.args.get("building_type")
    boroughs = request.args.get("boroughs").split(",")  # Split the boroughs by comma
    metrics = request.args.get("metrics", "").split(
        ","
    )  # Ensure metrics are split into a list
    output_format = request.args.get("output_format", "html")

    if not building_type or not boroughs or not metrics:
        return render_template(
            "report_result.html", message="Missing required parameters."
        )

    # --- Get data for report ---
    df, chart_data, table_html = generate_building_type_focus_data(
        building_type=building_type, boroughs=boroughs, metrics=metrics
    )

    # --- If no data, render fallback ---
    if df.empty:
        return render_template(
            "report_result.html", message="No data found for selected criteria."
        )

    # --- CSV Export ---
    if output_format == "csv":
        # Filter columns based on selected metrics
        columns_to_include = ["borough_name"]

        if "kwh" in metrics:
            columns_to_include.append("kwh")  # Use the actual column name

        if "peak_kw" in metrics:
            columns_to_include.append("peak_kw")  # Use the actual column name

        # Create a new DataFrame with only the selected columns
        df_selected_metrics = df[columns_to_include]

        # Rename columns for display in the CSV (if needed)
        df_selected_metrics.rename(
            columns={
                "borough_name": "Borough",  # Rename borough_name to Borough
                "kwh": "Average Annual Use (kWh)",
                "peak_kw": "Average Peak Demand (kW)",
            },
            inplace=True,
        )

        # Create the CSV export
        filename = f"Building_Type_Report_{building_type.replace(' ', '_')}.csv"
        return Response(
            df_selected_metrics.to_csv(index=False),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    # --- Render HTML with insights ---
    return render_template(
        "building_type_focus_report.html",
        building_type=building_type,
        boroughs=boroughs,
        metrics=metrics,
        chart_data=chart_data,
        table_html=table_html,
        now=datetime.now(),
    )

# -------------------- ESG NEW ROUTE WITH API --------------------
@bp.route("/esg")
def esg():
    """Get articles where 'energy' appears in the HEADLINE"""
    api_key = os.getenv("GUARDIAN_API_KEY")

    params = {
        "query-fields": "headline",  # ONLY search headlines
        "q": "UK AND energy",  # Must appear in headline
        "api-key": api_key,
        "show-fields": "headline,trailText",
        "page-size": 6,
        "order-by": "newest",
        "from-date": "2024-01-01",  # Last 1.5 years
    }
    try:
        response = requests.get(
            "https://content.guardianapis.com/search", params=params
        )
        response.raise_for_status()
        data = response.json()

        # Double-check headlines contain "energy" (case-insensitive)
        articles = [
            {
                "title": article["fields"]["headline"],
                "url": article["webUrl"],
                "summary": article["fields"]["trailText"],
                "published": article["webPublicationDate"][:10],
                "section": article["sectionName"],
            }
            for article in data.get("response", {}).get("results", [])
            if "energy" in article["fields"]["headline"].lower()
        ]

    except Exception as e:
        print(f"API Error: {str(e)}")
        articles = []

    # Add current timestamp for "Last updated"
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template("esg.html", articles=articles, last_updated=last_updated)
