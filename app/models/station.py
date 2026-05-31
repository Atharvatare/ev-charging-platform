from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship

class Station(SQLModel, table=True):
    __tablename__ = "stations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(nullable=False)
    address: str = Field(nullable=False)
    latitude: float = Field(nullable=False)
    longitude: float = Field(nullable=False)
    rating: float = Field(default=4.5)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ports: List["Port"] = Relationship(back_populates="station", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    solar_insights: List["SolarInsight"] = Relationship(back_populates="station", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Port(SQLModel, table=True):
    __tablename__ = "ports"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    station_id: UUID = Field(foreign_key="stations.id", nullable=False)
    connector_type: str = Field(nullable=False)  # "CCS2", "CHAdeMO", "Type 2 AC"
    power_kw: float = Field(nullable=False)      # e.g., 50.0, 150.0, 350.0
    price_per_kwh: float = Field(default=0.35)    # Price in USD per kWh
    status: str = Field(default="AVAILABLE")       # "AVAILABLE", "OCCUPIED", "CHARGING", "MAINTENANCE"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    station: Optional[Station] = Relationship(back_populates="ports", exclude=True)
    reservations: List["Reservation"] = Relationship(back_populates="port", exclude=True, sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class SolarInsight(SQLModel, table=True):
    __tablename__ = "solar_insights"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    station_id: UUID = Field(foreign_key="stations.id", nullable=False)
    solar_output_kw: float = Field(default=0.0)
    battery_storage_kwh: float = Field(default=0.0)
    renewable_percentage: int = Field(default=100) # Percentage of current charge powered by solar/wind
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    station: Optional[Station] = Relationship(back_populates="solar_insights", exclude=True)
