"""
Database models for the LEET (London Energy Efficiency Tool) app.

Defines SQLAlchemy ORM mappings for boroughs, building types, buildings,
and their associated energy usage metrics.

Tables:
    - Borough
    - BuildingType
    - Building
    - EnergyUsage

Dependencies:
    - SQLAlchemy 2.0 style typing and ORM
    - Flask-SQLAlchemy extension (for `db.Model`)
"""

from typing import List

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from leet_app import db


class Borough(db.Model):
    """Represents a London borough."""

    __tablename__ = "borough"

    borough_name: Mapped[str] = mapped_column(String, primary_key=True)

    # One borough has many buildings
    buildings: Mapped[List["Building"]] = relationship(
        back_populates="borough", lazy="select"
    )

    def __repr__(self):
        return f"<Borough {self.borough_name}>"


class BuildingType(db.Model):
    """Represents a type of building (e.g., Residential, Mixed-Use)."""

    __tablename__ = "building_type"

    building_type_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    building_type_name: Mapped[str] = mapped_column(String, nullable=False)

    # One building type is linked to many buildings
    buildings: Mapped[List["Building"]] = relationship(
        back_populates="building_type", lazy="select"
    )

    def __repr__(self):
        return f"<BuildingType {self.building_type_name}>"


class Building(db.Model):
    """Represents a building located in a borough, with geolocation and type info."""

    __tablename__ = "building"

    building_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    borough_name: Mapped[str] = mapped_column(
        ForeignKey("borough.borough_name", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    residential_count: Mapped[int] = mapped_column(Integer)
    non_residential_count: Mapped[int] = mapped_column(Integer)
    building_type_id: Mapped[int] = mapped_column(
        ForeignKey(
            "building_type.building_type_id", onupdate="CASCADE", ondelete="CASCADE"
        ),
        nullable=False,
    )

    # Relationships
    borough: Mapped["Borough"] = relationship(back_populates="buildings", lazy="select")
    building_type: Mapped["BuildingType"] = relationship(
        back_populates="buildings", lazy="select"
    )
    energy_usages: Mapped[List["EnergyUsage"]] = relationship(
        back_populates="building", lazy="select"
    )

    def __repr__(self):
        return f"<Building {self.building_id} in {self.borough_name}>"


class EnergyUsage(db.Model):
    """Represents energy metrics for a building."""

    __tablename__ = "energy_usage"

    usage_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(
        ForeignKey("building.building_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    kwh: Mapped[float] = mapped_column(Float)
    peak_kw: Mapped[float] = mapped_column(Float)

    # One usage entry belongs to one building
    building: Mapped["Building"] = relationship(
        back_populates="energy_usages", lazy="select"
    )

    def __repr__(self):
        return f"<EnergyUsage {self.usage_id} for Building {self.building_id}>"
