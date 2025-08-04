""" 
Utility functions for generating reports and visualisations in the Leet App.
This module provides functions to create summary statistics, charts, and maps
for energy usage data filtered by borough, building type, and other criteria.

Functions:
    - Data preparation for energy reports.
    - Generation of visualisations for inclusion in reports (e.g., maps, charts).
    - Report formatting. 
    
Dependencies:
    - pandas
    - plotly
    - Flask-SQLAlchemy
"""


import pandas as pd
import plotly.express as px
from leet_app import db
from leet_app.models import Building, BuildingType, EnergyUsage



def generate_borough_summary_data(borough, building_type, threshold):
    """
    Shared utility to retrieve, filter, and process borough summary data.

    Args:
        borough (str): Name of the borough to filter data by.
        building_type (str): Building type to filter data by (optional).
        threshold (float): Minimum kWh threshold to filter buildings by (optional).

    Returns:
        df (raw DataFrame),
        display_df (formatted),
        summary_stats (dict),
        column_names (list),
        table_data (records for table rendering)
    """

    # Base SQLAlchemy query
    stmt = (
        db.select(
            Building.building_id,
            Building.latitude,
            Building.longitude,
            BuildingType.building_type_name,
            EnergyUsage.kwh,
            EnergyUsage.peak_kw,
        )
        .join(EnergyUsage, Building.building_id == EnergyUsage.building_id)
        .join(BuildingType, BuildingType.building_type_id == Building.building_type_id)
        .filter(Building.borough_name == borough)
    )

    if building_type:
        stmt = stmt.filter(BuildingType.building_type_name == building_type)

    if threshold:
        stmt = stmt.filter(EnergyUsage.kwh >= threshold)

    df = pd.read_sql_query(stmt, db.engine)

    if df.empty:
        return None, None, None, None, None

    # Summary statistics (ensure unique buildings)
    total_buildings = df["building_id"].nunique()
    total_kwh = df["kwh"].sum()
    avg_kwh = df["kwh"].mean()
    avg_peak_kw = df["peak_kw"].mean()

    summary_stats = {
        "total_buildings": total_buildings,
        "total_kwh": total_kwh,
        "avg_kwh": avg_kwh,
        "avg_peak_kw": avg_peak_kw,
    }

    # Display-friendly DataFrame
    display_df = df.copy()
    display_df.drop(columns=["building_id"], inplace=True)

    display_df.rename(
        columns={
            "latitude": "Latitude",
            "longitude": "Longitude",
            "building_type_name": "Building Type",
            "kwh": "Annual Energy Use (kWh)",
            "peak_kw": "Peak Demand (kW)",
        },
        inplace=True,
    )

    display_df["Latitude"] = display_df["Latitude"].round(6)
    display_df["Longitude"] = display_df["Longitude"].round(6)
    display_df["Annual Energy Use (kWh)"] = display_df["Annual Energy Use (kWh)"].apply(
        lambda x: f"{round(x):,}"
    )
    display_df["Peak Demand (kW)"] = display_df["Peak Demand (kW)"].apply(
        lambda x: f"{x:,.2f}"
    )

    column_names = display_df.columns.tolist()
    table_data = display_df.to_dict(orient="records")

    return df, display_df, summary_stats, column_names, table_data


def generate_building_type_focus_data(building_type, boroughs, metrics):
    """
    Returns data to compare energy usage for a building type across selected boroughs.

    Args:
        building_type (str): Selected building type
        boroughs (list of str): Borough names
        metrics (list of str): Metrics to compare: 'kwh', 'peak_kw'

    Returns:
        df (raw DataFrame),
        chart_data (dict of Plotly chart HTMLs),
        table_html (formatted summary table)
    """

    stmt = (
        db.select(
            Building.borough_name,
            BuildingType.building_type_name,
            EnergyUsage.kwh,
            EnergyUsage.peak_kw,
        )
        .join(EnergyUsage, Building.building_id == EnergyUsage.building_id)
        .join(BuildingType, BuildingType.building_type_id == Building.building_type_id)
        .filter(BuildingType.building_type_name == building_type)
        .filter(Building.borough_name.in_(boroughs))
    )

    df = pd.read_sql_query(stmt, db.engine)

    if df.empty:
        return (
            df,
            {},
            "<p class='text-danger'>No data found for the selected filters.</p>",
        )

    # Group by borough and calculate average per metric
    summary = (
        df.groupby("borough_name").agg({"kwh": "mean", "peak_kw": "mean"}).reset_index()
    )

    summary.rename(
        columns={
            "borough_name": "Borough",
            "kwh": "Average Annual Use (kWh)",
            "peak_kw": "Average Peak Demand (kW)",
        },
        inplace=True,
    )

    print("[DEBUG] Selected Metrics:", metrics)

    # Create chart(s)
    chart_data = {}
    if "kwh" in metrics:
        fig_kwh = px.bar(
            summary,
            x="Borough",
            y="Average Annual Use (kWh)",
            title=f"Avg Annual Energy Use – {building_type}",
            labels={"Average Annual Use (kWh)": "kWh"},
            color="Borough",
        )
        chart_data["kwh"] = fig_kwh.to_html(full_html=False)

    if "peak_kw" in metrics:
        fig_peak = px.bar(
            summary,
            x="Borough",
            y="Average Peak Demand (kW)",
            title=f"Avg Peak Demand – {building_type}",
            labels={"Average Peak Demand (kW)": "kW"},
            color="Borough",
        )
        chart_data["peak_kw"] = fig_peak.to_html(full_html=False)

    # Generate table HTML
    table_html = summary.to_html(
        classes="table table-striped text-center", index=False, justify="center"
    )

    return df, chart_data, table_html

def create_report_geomap(df, borough):
    """
    Creates a scatter mapbox of energy demand distribution for a specified borough.

    Args:
        df (pandas.DataFrame): DataFrame with building data, including latitude, longitude, 
        energy usage (kWh),building type, and peak energy demand.
        borough (str): Borough name for which the energy demand map is generated.

    Returns:
        str: HTML representation of the map for the borough report, to be embedded in a webpage.
    """
    if df.empty:
        return None

    fig = px.scatter_map(
        df,
        lat="latitude",
        lon="longitude",
        size="kwh",
        color="kwh",
        hover_data=["building_type_name", "kwh", "peak_kw"],
        color_continuous_scale="Viridis",
        zoom=11,
        map_style="carto-positron",
        title=f"Energy Demand Distribution in {borough}",
        height=500,
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})

    return fig.to_html(full_html=False)
