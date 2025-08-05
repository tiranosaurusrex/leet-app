"""
Data ingestion script for LEET (London Energy Efficiency Tool).

Reads a prepared CSV and populates the database tables: Borough, BuildingType,
Building, and EnergyUsage using SQLAlchemy ORM.

Dependencies:
    - pandas
    - SQLAlchemy
    - Flask-SQLAlchemy
    - importlib.resources (for locating the CSV within the package)
"""
from importlib import resources
import pandas as pd
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError


from leet_app.extensions import db
from leet_app.models import Borough, BuildingType, Building, EnergyUsage


def clean_dataframe(df):
    """Strip whitespace from categorical columns."""
    df['BOROUGH'] = df['BOROUGH'].str.strip()
    df['BUILDING_TYPE'] = df['BUILDING_TYPE'].str.strip()
    return df


def add_boroughs(df):
    """Add unique boroughs to the database."""
    try:
        for borough in df['BOROUGH'].unique():
            if not db.session.get(Borough, borough):
                db.session.add(Borough(borough_name=borough))
        db.session.commit()
        print("[INFO] Boroughs added.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[ERROR] Failed to add boroughs: {e}")


def add_building_types(df):
    """Add unique building types to the database."""
    try:
        for btype in df['BUILDING_TYPE'].unique():
            exists = db.session.query(BuildingType).filter_by(building_type_name=btype).first()
            if not exists:
                db.session.add(BuildingType(building_type_name=btype))
        db.session.commit()
        print("[INFO] Building types added.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[ERROR] Failed to add building types: {e}")


def add_buildings_and_energy(df):
    """Add buildings and their corresponding energy usage."""
    try:
        # Create lookup map for FK
        type_map = {
            bt.building_type_name: bt.building_type_id
            for bt in BuildingType.query.all()
        }

        for index, row in df.iterrows():
            try:
                building = Building(
                    borough_name=row['BOROUGH'],
                    latitude=row['LATITUDE'],
                    longitude=row['LONGITUDE'],
                    residential_count=row['RESI_COUNT'],
                    non_residential_count=row['NONRESI_COUNT'],
                    building_type_id=type_map[row['BUILDING_TYPE']]
                )
                db.session.add(building)
                db.session.flush()  # assign Building_ID

                usage = EnergyUsage(
                    building_id=building.building_id,
                    kwh=row['KWH'],
                    peak_kw=row['PEAK_KW']
                )
                db.session.add(usage)

            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"[WARN] Skipped row {index} due to: {e}")
            else:
                db.session.commit()

        print("[INFO] Buildings and energy usage added.")

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[ERROR] Failed bulk insert for buildings: {e}")


def add_all_data():
    """Main function to load CSV and insert all data into the database."""
    try:
        # Locate CSV within src/data/
        csv_path = resources.files("data").joinpath("prepared_heat_demand_data.csv")
        print(f"[DEBUG] Loading CSV from: {csv_path}")

        df = pd.read_csv(csv_path)
        df = clean_dataframe(df)

        tables_and_functions = [
            (Borough, add_boroughs),
            (BuildingType, add_building_types),
            (Building, add_buildings_and_energy),
        ]

        for model, func_ in tables_and_functions:
            count = db.session.execute(db.select(func.count()).select_from(model)).scalar()
            if count == 0:
                func_(df)
            else:
                print(f"[INFO] Table '{model.__tablename__}' already has data.")

    except FileNotFoundError as e:
        print(f"[ERROR] CSV file not found: {e}")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[ERROR] SQLAlchemy error during data loading: {e}")
