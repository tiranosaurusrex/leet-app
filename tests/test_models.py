"""
Unit tests for SQLAlchemy models used in the LEET app.
Tests cover object creation, table relationships, and __repr__ methods.
"""

import pytest
from leet_app import db
from leet_app.models import Borough, BuildingType, Building, EnergyUsage


def test_create_borough(app):
    """
    GIVEN the Borough model
    WHEN a new borough is added to the database
    THEN it should be queryable by its primary key
    """
    with app.app_context():
        borough = Borough(borough_name="Camden")
        db.session.add(borough)
        db.session.commit()

        result = db.session.get(Borough, "Camden")
        assert result is not None
        assert result.borough_name == "Camden"


def test_create_building_type(app):
    """
    GIVEN the BuildingType model
    WHEN a new building type is added
    THEN it should be assigned an auto-incremented ID and be queryable
    """
    with app.app_context():
        bt = BuildingType(building_type_name="Residential")
        db.session.add(bt)
        db.session.commit()

        assert bt.building_type_id is not None
        fetched = db.session.get(BuildingType, bt.building_type_id)
        assert fetched.building_type_name == "Residential"


def test_create_building_with_relationships(app):
    """
    GIVEN a Borough and BuildingType
    WHEN a new Building is created with foreign keys
    THEN the building should be associated with the correct borough and type
    """
    with app.app_context():
        borough = Borough(borough_name="Westminster")
        btype = BuildingType(building_type_name="Mixed-Use")
        db.session.add_all([borough, btype])
        db.session.commit()

        building = Building(
            borough_name="Westminster",
            latitude=51.5,
            longitude=-0.1,
            residential_count=3,
            non_residential_count=2,
            building_type_id=btype.building_type_id,
        )
        db.session.add(building)
        db.session.commit()

        assert building.borough.borough_name == "Westminster"
        assert building.building_type.building_type_name == "Mixed-Use"


def test_add_energy_usage(app):
    """
    GIVEN a Building
    WHEN EnergyUsage is added
    THEN it should be associated with that building
    """
    with app.app_context():
        borough = Borough(borough_name="Hackney")
        btype = BuildingType(building_type_name="Non-Residential")
        db.session.add_all([borough, btype])
        db.session.commit()

        building = Building(
            borough_name="Hackney",
            latitude=51.55,
            longitude=-0.06,
            residential_count=0,
            non_residential_count=10,
            building_type_id=btype.building_type_id,
        )
        db.session.add(building)
        db.session.commit()

        usage = EnergyUsage(
            building_id=building.building_id,
            kwh=12345.67,
            peak_kw=89.5
        )
        db.session.add(usage)
        db.session.commit()

        assert usage.building.building_id == building.building_id
        assert usage.kwh == 12345.67
        assert len(building.energy_usages) == 1


def test_model_repr_methods(app):
    """
    GIVEN instances of each model
    WHEN __repr__ is called
    THEN it should return a human-readable string
    """
    with app.app_context():
        borough = Borough(borough_name="City of London")
        bt = BuildingType(building_type_name="Unknown")
        db.session.add_all([borough, bt])
        db.session.commit()

        building = Building(
            borough_name="City of London",
            latitude=51.51,
            longitude=-0.09,
            residential_count=5,
            non_residential_count=0,
            building_type_id=bt.building_type_id,
        )
        db.session.add(building)
        db.session.commit()

        usage = EnergyUsage(building_id=building.building_id, kwh=50000, peak_kw=70)
        db.session.add(usage)
        db.session.commit()

        assert repr(borough) == "<Borough City of London>"
        assert repr(bt) == "<BuildingType Unknown>"
        assert repr(building).startswith("<Building")
        assert repr(usage).startswith("<EnergyUsage")