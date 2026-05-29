from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, text
from app.core.database import get_session
from app.models.station import Station, Port, SolarInsight
from app.routers.auth import get_current_user, require_role
from app.models.user import User
from app.ws.connection_manager import manager

router = APIRouter(prefix="/api/stations", tags=["Charging Stations"])

@router.get("/", response_model=List[Station])
def list_stations(session: Session = Depends(get_session)):
    """Retrieves all EV charging stations with pre-loaded relations."""
    stations = session.exec(select(Station)).all()
    # Simple trick to resolve relationships eagerly for schema output
    for st in stations:
        st.ports
        st.solar_insights
    return stations

@router.get("/nearby")
def get_nearby_stations(
    latitude: float = Query(..., description="User's current latitude coordinate"),
    longitude: float = Query(..., description="User's current longitude coordinate"),
    radius_meters: float = Query(5000.0, description="Search radius in meters"),
    session: Session = Depends(get_session)
):
    """
    Executes a high-speed PostGIS spatial query to calculate spherical distance 
    between station coordinates and the user's location, returning sorted results 
    within the target search radius.
    """
    # SQL query utilizing ST_DistanceSphere on standard lat/long coordinates.
    # Note: ST_MakePoint takes (longitude, latitude) as standard GeoJSON order.
    query_str = text("""
        SELECT s.id, s.name, s.address, s.latitude, s.longitude, s.rating,
               ST_DistanceSphere(
                   ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326),
                   ST_SetSRID(ST_MakePoint(:user_lng, :user_lat), 4326)
               ) AS distance_meters
        FROM stations s
        WHERE ST_DistanceSphere(
            ST_SetSRID(ST_MakePoint(s.longitude, s.latitude), 4326),
            ST_SetSRID(ST_MakePoint(:user_lng, :user_lat), 4326)
        ) <= :radius
        ORDER BY distance_meters ASC
    """)
    
    results = session.execute(query_str, {
        "user_lng": longitude,
        "user_lat": latitude,
        "radius": radius_meters
    }).fetchall()
    
    nearby = []
    for row in results:
        station_id = UUID(str(row[0]))
        station = session.get(Station, station_id)
        
        # Load relationships
        ports_list = [
            {
                "id": p.id,
                "connector_type": p.connector_type,
                "power_kw": p.power_kw,
                "price_per_kwh": p.price_per_kwh,
                "status": p.status
            }
            for p in station.ports
        ]
        
        solar = None
        if station.solar_insights:
            si = station.solar_insights[0]
            solar = {
                "solar_output_kw": si.solar_output_kw,
                "battery_storage_kwh": si.battery_storage_kwh,
                "renewable_percentage": si.renewable_percentage
            }
            
        nearby.append({
            "id": station.id,
            "name": station.name,
            "address": station.address,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "rating": station.rating,
            "distance_meters": round(row[6], 1),
            "ports": ports_list,
            "solar_insights": solar
        })
        
    return nearby

@router.get("/{station_id}")
def get_station_details(station_id: UUID, session: Session = Depends(get_session)):
    """Retrieves full telemetry, ports, and renewable energy metrics of a specific station."""
    station = session.get(Station, station_id)
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    
    # Eagerly map relationships for customized response output
    ports = [
        {
            "id": p.id,
            "connector_type": p.connector_type,
            "power_kw": p.power_kw,
            "price_per_kwh": p.price_per_kwh,
            "status": p.status
        }
        for p in station.ports
    ]
    
    solar = None
    if station.solar_insights:
        si = station.solar_insights[0]
        solar = {
            "id": si.id,
            "solar_output_kw": si.solar_output_kw,
            "battery_storage_kwh": si.battery_storage_kwh,
            "renewable_percentage": si.renewable_percentage,
            "updated_at": si.updated_at
        }
        
    return {
        "id": station.id,
        "name": station.name,
        "address": station.address,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "rating": station.rating,
        "ports": ports,
        "solar_insights": solar
    }

@router.patch("/{station_id}/ports/{port_id}/status")
async def update_port_status(
    station_id: UUID, 
    port_id: UUID, 
    new_status: str, 
    session: Session = Depends(get_session),
    admin_user: User = Depends(require_role(["admin"]))
):
    """
    Allows system administrators or OCPP simulated charge points to update a port's operational status.
    Triggers database update and handles WebSocket broadcast alerts.
    """
    port = session.exec(
        select(Port).where(Port.id == port_id, Port.station_id == station_id)
    ).first()
    
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Connector Port not found on this station"
        )
        
    allowed_statuses = ["AVAILABLE", "OCCUPIED", "CHARGING", "MAINTENANCE", "FAULTED"]
    if new_status.upper() not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid status. Must be one of: {allowed_statuses}"
        )
        
    port.status = new_status.upper()
    port.updated_at = datetime.utcnow()
    session.add(port)
    session.commit()
    session.refresh(port)
    
    # Real-time WebSocket broadcast to update all active map markers and operator grids
    await manager.broadcast({
        "type": "PORT_STATUS_UPDATE",
        "station_id": str(station_id),
        "port_id": str(port_id),
        "status": port.status
    })
    
    return {"message": "Port status updated successfully", "port_id": port.id, "status": port.status}

@router.post("/reseed")
def reseed_database_endpoint(
    session: Session = Depends(get_session),
    admin_user: User = Depends(require_role(["admin"]))
):
    """
    Exposes an administrative route to force-clear and re-seed the charging stations grid
    representing the latest pan-India hubs.
    """
    from app.core.seed import seed_database
    seed_database(force=True)
    return {"message": "Database successfully force-reseeded with newest Pan-India stations!"}
