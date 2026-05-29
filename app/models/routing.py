from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

class RouteTrip(SQLModel, table=True):
    __tablename__ = "route_trips"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    origin_name: str = Field(nullable=False)
    destination_name: str = Field(nullable=False)
    origin_lat: float = Field(nullable=False)
    origin_lng: float = Field(nullable=False)
    destination_lat: float = Field(nullable=False)
    destination_lng: float = Field(nullable=False)
    start_soc: float = Field(default=100.0)             # Vehicle battery SoC % at start
    predicted_arrival_soc: float = Field(default=0.0)    # predicted final battery SoC %
    actual_arrival_soc: Optional[float] = Field(default=None)
    route_geometry_json: str = Field(nullable=False)     # GeoJSON path coordinates
    created_at: datetime = Field(default_factory=datetime.utcnow)
