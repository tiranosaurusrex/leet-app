"""
Energy Data Visualization Module for LEET (London Energy Efficiency Tool).

This module provides Plotly-based visualizations of energy usage across Central London.
It uses SQLAlchemy to query a normalized SQLite database and returns HTML-embedded charts.

Visualisations:
    - Total building counts by borough and building type.
    - Average energy use per borough filtered by building type and metric.
    - Energy demand maps (geomap and heatmap).
    - Borough-specific energy distribution (pie chart).
    - Identification of high energy demand buildings.

Charts are styled for clarity and consistency using the "ggplot2" template.

Dependencies:
    - pandas
    - plotly.express
    - sqlalchemy (via Flask-SQLAlchemy)
"""

import pandas as pd
import plotly.express as px

from src.leet_app.extensions import db
from src.leet_app.models import Borough, Building, BuildingType, EnergyUsage


def building_count_chart():
    """
    Creates a bar chart showing the number of buildings by borough and building type.
    Returns Plotly HTML to embed in template.
    """
    stmt = (
        db.select(
            Borough.borough_name,
            BuildingType.building_type_name,
            db.func.count(Building.building_id).label("total_buildings"),
        )
        .join(Building, Borough.borough_name == Building.borough_name)
        .join(BuildingType, BuildingType.building_type_id == Building.building_type_id)
        .group_by(Borough.borough_name, BuildingType.building_type_name)
    )

    df = pd.read_sql_query(stmt, db.engine)

    fig = px.bar(
        df,
        x="borough_name",
        y="total_buildings",
        color="building_type_name",
        barmode="group",
        title="Total Buildings by Borough and Type",
        labels={
            "borough_name": "Borough",
            "building_type_name": "Building Type",
            "total_buildings": "Number of Buildings",
        },
        template="ggplot2",
    )

    fig.update_layout(
        title_font_size=20, margin=dict(l=40, r=40, t=60, b=40), height=500
    )
    return {"fig": fig.to_html(full_html=False, include_plotlyjs="cdn")}


def create_avg_energy_chart(metric, building_type_filter):
    """
    Generates a bar chart of average energy metric per borough for a given building type.

    Args:
        metric (str): 'kwh' or 'peak_kw'.
        building_type_filter (str): Building type to filter the data.

    Returns:
        dict: HTML representation of the Plotly figure.
    """
    stmt = (
        db.select(Borough.borough_name, getattr(EnergyUsage, metric).label("value"))
        .join(Building, Borough.borough_name == Building.borough_name)
        .join(EnergyUsage, Building.building_id == EnergyUsage.building_id)
        .join(BuildingType, BuildingType.building_type_id == Building.building_type_id)
        .where(BuildingType.building_type_name == building_type_filter)
    )

    df = pd.read_sql_query(stmt, db.engine)
    df_avg = df.groupby("borough_name", as_index=False)["value"].mean()

    fig = px.bar(
        df_avg,
        x="borough_name",
        y="value",
        labels={"value": f"Average {metric.upper()}", "borough_name": "Borough"},
        title=f"Average {metric.upper()} for {building_type_filter} Buildings by Borough",
        template="ggplot2",
        color="borough_name",
    )

    fig.update_traces(marker_line_width=1, marker_line_color="black")
    fig.update_layout(
        showlegend=False,
        title_font_size=20,
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
    )

    return {"fig": fig.to_html(full_html=False, include_plotlyjs="cdn")}


def create_geomap_figure(metric, building_type_filter):
    """
    Creates a geomap figure based on selected metric and building type.

    Args:
        metric (str): Metric (e.g., 'kwh', 'peak_kw') to display on map.
        building_type_filter (str): Building type to filter the data.

    Returns:
        str: HTML string representation of the geomap.
    """
    stmt = (
        db.select(
            Building.latitude,
            Building.longitude,
            getattr(EnergyUsage, metric).label(metric),
        )
        .join(EnergyUsage)
        .join(BuildingType)
        .where(BuildingType.building_type_name == building_type_filter)
    )

    df = pd.read_sql_query(stmt, db.engine)

    if df.empty:
        return px.scatter_map(title="No data available for selected filters")

    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        size=metric,
        color=metric,
        zoom=10,
        map_style="carto-positron",
        title=f"Energy Demand Map: {building_type_filter} buildings ({metric})",
    )
    fig.update_layout(
        title_font_size=20, margin=dict(l=40, r=40, t=60, b=40), height=500
    )
    return fig.to_html(full_html=False)


def generate_pie_chart_by_borough(selected_borough):
    """
    Generates a pie chart of energy usage by building type for a selected borough.

    Args:
        selected_borough (str): Borough name to filter the data.

    Returns:
        Plotly figure: Pie chart of energy usage by building type.
    """
    stmt = (
        db.select(
            Building.building_type_id, EnergyUsage.kwh, BuildingType.building_type_name
        )
        .join(EnergyUsage, Building.building_id == EnergyUsage.building_id)
        .join(BuildingType, Building.building_type_id == BuildingType.building_type_id)
        .where(Building.borough_name == selected_borough)
    )

    df = pd.read_sql_query(stmt, db.engine)

    if df.empty:
        return px.pie(
            names=["No data"], values=[1], title=f"No data for {selected_borough}"
        )

    pie_df = df.groupby("building_type_name")["kwh"].sum().reset_index()

    fig = px.pie(
        pie_df,
        names="building_type_name",
        values="kwh",
        title=f"Energy Use by Building Type in {selected_borough}",
        hole=0.4,
        template="ggplot2",
    )
    fig.update_layout(
        title_font_size=20, margin=dict(l=40, r=40, t=60, b=40), height=500
    )
    return fig


def create_energy_heatmap(borough):
    """
    Creates an energy heatmap of energy usage within a given borough.

    Args:
        borough (str): Borough name for the heatmap.

    Returns:
        Plotly figure: Heatmap of energy usage for the selected borough.
    """
    stmt = (
        db.select(Building.latitude, Building.longitude, EnergyUsage.kwh)
        .join(EnergyUsage)
        .filter(Building.borough_name == borough)
    )
    df = pd.read_sql_query(stmt, db.engine)

    if df.empty:
        return px.scatter_map(
            lat=[51.5074],
            lon=[-0.1278],
            zoom=10,
            map_style="carto-positron",
            title=f"No data available for {borough}",
        )

    fig = px.density_map(
        df,
        lat="latitude",
        lon="longitude",
        z="kwh",
        radius=20,
        center=dict(lat=51.5074, lon=-0.1278),
        zoom=10,
        map_style="carto-positron",
        title=f"Energy Demand Density in {borough}",
    )
    fig.update_layout(
        title_font_size=20, margin=dict(l=40, r=40, t=60, b=40), height=500
    )
    return fig


def create_high_demand_chart(threshold_kwh):
    """
    Creates a bar chart of high energy demand buildings based on a given threshold.

    Args:
        threshold_kwh (float): Threshold for energy consumption (kWh).

    Returns:
        Plotly figure: Bar chart of high demand buildings.
    """
    stmt = db.select(Building.borough_name, EnergyUsage.kwh).join(EnergyUsage)
    df = pd.read_sql_query(stmt, db.engine)

    high_demand_df = df[df["kwh"] > threshold_kwh]

    demand_counts = high_demand_df["borough_name"].value_counts().reset_index()
    demand_counts.columns = ["borough_name", "high_demand_count"]

    if demand_counts.empty:
        demand_counts = pd.DataFrame(
            {
                "borough_name": df["borough_name"].unique(),
                "high_demand_count": [0] * len(df["borough_name"].unique()),
            }
        )

    fig = px.bar(
        demand_counts,
        x="borough_name",
        y="high_demand_count",
        color="borough_name",
        title=f"High-Energy Demand Buildings (KWH > {threshold_kwh:,.0f})",
        labels={"borough_name": "Borough", "high_demand_count": "High Demand Count"},
        template="ggplot2",
    )
    fig.update_layout(
        title_font_size=20, margin=dict(l=40, r=40, t=60, b=40), height=500
    )
    return fig
