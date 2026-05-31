import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.routing import RouteTrip
from app.engines.router import compute_route, SF_GRAPH_NODES

router = APIRouter(prefix="/api/routing", tags=["Route Optimization"])

class RoutePlanRequest(BaseModel):
    origin: str
    destination: str
    start_soc: float = 100.0
    vehicle: Optional[str] = "tata_nexon_ev_max"
    temperature_c: Optional[float] = 25.0
    wind_speed_kmh: Optional[float] = 0.0
    wind_direction: Optional[str] = "none"
    rain: Optional[str] = "none"

class IsorangeRequest(BaseModel):
    origin: str
    start_soc: float = 100.0
    vehicle: Optional[str] = "tata_nexon_ev_max"
    temperature_c: Optional[float] = 25.0
    wind_speed_kmh: Optional[float] = 0.0
    wind_direction: Optional[str] = "none"
    rain: Optional[str] = "none"


@router.get("/nodes")
def get_graph_nodes():
    """Returns a list of all supported SF road network intersections and stations with coordinates."""
    nodes = []
    for name, data in SF_GRAPH_NODES.items():
        nodes.append({
            "id": name,
            "display_name": name.replace("_", " "),
            "latitude": data["lat"],
            "longitude": data["lng"],
            "elevation": data["elev"],
            "type": data["type"]
        })
    return nodes

@router.post("/plan")
def plan_optimized_route(
    req: RoutePlanRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Solves A* topography routing and calculates predicted battery consumption. 
    Saves the trip metadata and dynamic path geometry details in the database logs.
    """
    try:
        from app.engines.battery import VEHICLE_PROFILES, EVEnergyModel
        
        # Load the selected vehicle's physical characteristics
        profile = VEHICLE_PROFILES.get(req.vehicle, VEHICLE_PROFILES["tata_nexon_ev_max"])
        ev_model = EVEnergyModel(
            mass_kg=profile["mass_kg"],
            drag_coeff=profile["drag_coeff"],
            frontal_area=profile["frontal_area"],
            rolling_coeff=profile["rolling_coeff"],
            battery_capacity_kwh=profile["battery_capacity_kwh"],
            efficiency=profile["efficiency"],
            regen_efficiency=profile["regen_efficiency"],
            auxiliary_draw_w=profile["auxiliary_draw_w"],
            temperature_c=req.temperature_c,
            wind_speed_kmh=req.wind_speed_kmh,
            wind_direction=req.wind_direction,
            rain=req.rain
        )
        
        route_results = compute_route(
            origin=req.origin,
            destination=req.destination,
            start_soc=req.start_soc,
            ev_model=ev_model
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if "error" in route_results:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=route_results["error"])

    # Extract coordinates list for GeoJSON format
    coords = []
    for point in route_results["telemetry"]:
        coords.append([point["lng"], point["lat"]])

    geojson_geom = {
        "type": "LineString",
        "coordinates": coords
    }

    # Save trip to database RouteTrip log
    trip = RouteTrip(
        user_id=current_user.id,
        origin_name=req.origin.replace("_", " "),
        destination_name=req.destination.replace("_", " "),
        origin_lat=SF_GRAPH_NODES[req.origin]["lat"],
        origin_lng=SF_GRAPH_NODES[req.origin]["lng"],
        destination_lat=SF_GRAPH_NODES[req.destination]["lat"],
        destination_lng=SF_GRAPH_NODES[req.destination]["lng"],
        start_soc=req.start_soc,
        predicted_arrival_soc=route_results["final_soc"],
        route_geometry_json=json.dumps(geojson_geom)
    )
    
    session.add(trip)
    session.commit()
    session.refresh(trip)

    # Return results enriched with DB Trip ID
    route_results["trip_id"] = trip.id
    return route_results


@router.get("/history", response_model=List[RouteTrip])
def list_trip_history(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all past saved topography-aware optimized trip logs for the authenticated driver."""
    trips = session.exec(
        select(RouteTrip)
        .where(RouteTrip.user_id == current_user.id)
    ).all()
    return trips


@router.post("/compare")
def compare_fleet_routing(
    req: RoutePlanRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Simulates and compares topographic route depletions, charging stops, travel costs,
    and carbon offset statistics for all 5 vehicle profiles in parallel.
    """
    from app.engines.battery import VEHICLE_PROFILES, EVEnergyModel
    
    comparisons = []
    
    for key, profile in VEHICLE_PROFILES.items():
        try:
            ev_model = EVEnergyModel(
                mass_kg=profile["mass_kg"],
                drag_coeff=profile["drag_coeff"],
                frontal_area=profile["frontal_area"],
                rolling_coeff=profile["rolling_coeff"],
                battery_capacity_kwh=profile["battery_capacity_kwh"],
                efficiency=profile["efficiency"],
                regen_efficiency=profile["regen_efficiency"],
                auxiliary_draw_w=profile["auxiliary_draw_w"],
                temperature_c=req.temperature_c,
                wind_speed_kmh=req.wind_speed_kmh,
                wind_direction=req.wind_direction,
                rain=req.rain
            )
            
            res = compute_route(
                origin=req.origin,
                destination=req.destination,
                start_soc=req.start_soc,
                ev_model=ev_model
            )
            
            if "error" in res:
                continue
                
            # Compute estimated charging costs (₹100 deposit + ₹18.5/kWh charging if re-routed)
            charging_cost = 0.0
            if res.get("rerouted", False):
                energy_recharged = 0.73 * profile["battery_capacity_kwh"]
                charging_cost = 100.00 + (energy_recharged * 18.50)
                
            # Sum up actual total energy spent from telemetry segments
            energy_spent = sum(max(0.0, pt.get("energy_consumed_kwh", 0.0)) for pt in res["telemetry"])
                
            comparisons.append({
                "vehicle_id": key,
                "display_name": profile["display_name"],
                "total_distance_km": res["total_distance_km"],
                "total_duration_mins": res["total_duration_mins"],
                "final_soc": res["final_soc"],
                "energy_consumed_kwh": round(energy_spent, 2),
                "carbon_saved_kg": round(res["total_distance_km"] * 0.12, 1),
                "stops": 1 if res.get("rerouted", False) else 0,
                "cost": round(charging_cost, 2)
            })
        except Exception as e:
            continue
            
    return comparisons


@router.post("/isorange")
def calculate_isorange_contour(
    req: IsorangeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Computes all reachable nodes (SoC >= 10.0%) from origin given EV profile and environmental overrides.
    Sorts coordinates by polar angle to construct a standard GeoJSON Polygon closed loop.
    """
    import math
    import heapq
    from app.engines.battery import VEHICLE_PROFILES, EVEnergyModel
    from app.engines.router import build_road_network

    if req.origin not in SF_GRAPH_NODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Origin node is outside network coverage.")

    try:
        profile = VEHICLE_PROFILES.get(req.vehicle, VEHICLE_PROFILES["tata_nexon_ev_max"])
        ev_model = EVEnergyModel(
            mass_kg=profile["mass_kg"],
            drag_coeff=profile["drag_coeff"],
            frontal_area=profile["frontal_area"],
            rolling_coeff=profile["rolling_coeff"],
            battery_capacity_kwh=profile["battery_capacity_kwh"],
            efficiency=profile["efficiency"],
            regen_efficiency=profile["regen_efficiency"],
            auxiliary_draw_w=profile["auxiliary_draw_w"],
            temperature_c=req.temperature_c,
            wind_speed_kmh=req.wind_speed_kmh,
            wind_direction=req.wind_direction,
            rain=req.rain
        )
        
        graph = build_road_network(ev_model)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Dijkstra traversal to maximize remaining SoC
    pq = [(-req.start_soc, req.origin)]
    max_soc = {node: -1.0 for node in graph.nodes}
    max_soc[req.origin] = req.start_soc
    
    while pq:
        neg_soc, current_node = heapq.heappop(pq)
        current_soc = -neg_soc
        
        if current_soc < max_soc[current_node]:
            continue
            
        for neighbor in graph.neighbors(current_node):
            edge_data = graph[current_node][neighbor]
            energy_kwh = edge_data["energy"]
            soc_loss = (energy_kwh / ev_model.capacity) * 100.0
            next_soc = current_soc - soc_loss
            next_soc = min(max(next_soc, 0.0), 100.0)
            
            if next_soc > max_soc[neighbor]:
                max_soc[neighbor] = next_soc
                heapq.heappush(pq, (-next_soc, neighbor))

    # Filter reachable nodes (SoC >= 10.0%)
    reachable_nodes = [node for node, val in max_soc.items() if val >= 10.0]

    origin_lat = SF_GRAPH_NODES[req.origin]["lat"]
    origin_lng = SF_GRAPH_NODES[req.origin]["lng"]

    # Extract coordinates for reachable boundary
    boundary_coords = []
    for node in reachable_nodes:
        if node == req.origin:
            continue
        lat = SF_GRAPH_NODES[node]["lat"]
        lng = SF_GRAPH_NODES[node]["lng"]
        boundary_coords.append((lng, lat))

    # Fallback if fewer than 3 boundary nodes are reachable
    if len(boundary_coords) < 3:
        fallback_coords = []
        for i in range(12):
            angle = (i * 30.0) * (math.pi / 180.0)
            lat = origin_lat + 0.02 * math.sin(angle)
            lng = origin_lng + 0.02 * math.cos(angle)
            fallback_coords.append([lng, lat])
        fallback_coords.append(fallback_coords[0])  # Close ring
        
        geojson_geom = {
            "type": "Polygon",
            "coordinates": [fallback_coords]
        }
    else:
        # Sort boundary coordinates by polar angle relative to the origin coordinate
        def get_polar_angle(coord):
            lng, lat = coord
            return math.atan2(lat - origin_lat, lng - origin_lng)

        boundary_coords.sort(key=get_polar_angle)
        
        polygon_coords = [[lng, lat] for lng, lat in boundary_coords]
        polygon_coords.append(polygon_coords[0])  # Close ring
        
        geojson_geom = {
            "type": "Polygon",
            "coordinates": [polygon_coords]
        }

    return {
        "reachable_nodes": reachable_nodes,
        "max_soc": {k: round(v, 2) for k, v in max_soc.items() if v >= 10.0},
        "geojson": geojson_geom
    }


