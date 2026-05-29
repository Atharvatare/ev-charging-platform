import networkx as nx
from typing import Dict, Any, List, Tuple
from app.engines.battery import EVEnergyModel, default_ev_model

# Definition of nodes in the SF road network with latitude, longitude, and elevation
SF_GRAPH_NODES = {
    "Rincon_Center": {"lat": 37.7915, "lng": -122.3923, "elev": 5.0, "type": "station"},
    "Union_Square": {"lat": 37.7865, "lng": -122.4098, "elev": 15.0, "type": "station"},
    "Salesforce_Transit": {"lat": 37.7892, "lng": -122.3970, "elev": 6.0, "type": "station"},
    "Civic_Center": {"lat": 37.7798, "lng": -122.4178, "elev": 14.0, "type": "station"},
    "Mission_District": {"lat": 37.7554, "lng": -122.4190, "elev": 20.0, "type": "station"},
    "Golden_Gate_Park": {"lat": 37.7702, "lng": -122.4702, "elev": 65.0, "type": "station"},
    "Embarcadero": {"lat": 37.8000, "lng": -122.3980, "elev": 2.0, "type": "road"},
    "Chinatown": {"lat": 37.7940, "lng": -122.4080, "elev": 45.0, "type": "road"},
    "Nob_Hill": {"lat": 37.7930, "lng": -122.4140, "elev": 110.0, "type": "road"},
    "SOMA": {"lat": 37.7780, "lng": -122.4050, "elev": 8.0, "type": "road"},
    "Castro": {"lat": 37.7620, "lng": -122.4350, "elev": 40.0, "type": "road"},
    "Richmond_District": {"lat": 37.7780, "lng": -122.4850, "elev": 50.0, "type": "road"},
    "Sunset_District": {"lat": 37.7500, "lng": -122.4850, "elev": 40.0, "type": "road"},
    "Twin_Peaks": {"lat": 37.7540, "lng": -122.4470, "elev": 280.0, "type": "road"}
}

# Driving connections (edges) with physical distances (km) and base limits (km/h)
SF_GRAPH_EDGES = [
    # Downtown grid
    ("Embarcadero", "Rincon_Center", 1.1, 40),
    ("Rincon_Center", "Salesforce_Transit", 0.6, 35),
    ("Salesforce_Transit", "SOMA", 1.3, 45),
    ("Salesforce_Transit", "Union_Square", 1.2, 40),
    ("Embarcadero", "Chinatown", 1.2, 35),
    
    # Chinatown & Nob Hill steep sections
    ("Chinatown", "Union_Square", 0.9, 30),
    ("Chinatown", "Nob_Hill", 0.7, 30),
    ("Union_Square", "Nob_Hill", 0.8, 30),
    ("Nob_Hill", "Civic_Center", 1.8, 40),
    
    # SOMA to Mission & Civic Center
    ("SOMA", "Civic_Center", 1.2, 45),
    ("SOMA", "Mission_District", 2.6, 50),
    ("Civic_Center", "Castro", 2.2, 45),
    ("Mission_District", "Castro", 1.8, 40),
    
    # Hills & Outer Districts
    ("Castro", "Twin_Peaks", 2.1, 45),
    ("Twin_Peaks", "Sunset_District", 3.8, 50),
    ("Civic_Center", "Golden_Gate_Park", 4.9, 60),
    ("Golden_Gate_Park", "Richmond_District", 1.4, 45),
    ("Golden_Gate_Park", "Sunset_District", 2.5, 45),
    ("Richmond_District", "Sunset_District", 3.2, 50)
]

def build_road_network(ev_model: EVEnergyModel) -> nx.DiGraph:
    """Builds a NetworkX directed graph populated with real dynamic physics edge weights."""
    g = nx.DiGraph()
    
    # Add Nodes with elevations and types
    for node, data in SF_GRAPH_NODES.items():
        g.add_node(node, lat=data["lat"], lng=data["lng"], elev=data["elev"], type=data["type"])
        
    # Add Edges (in both directions for realistic bi-directional transit)
    for u, v, dist, speed in SF_GRAPH_EDGES:
        # Elevation differences
        elev_u = SF_GRAPH_NODES[u]["elev"]
        elev_v = SF_GRAPH_NODES[v]["elev"]
        
        # Segment energy attributes (U to V)
        u_to_v_energy = ev_model.calculate_energy_consumption(dist, speed, elev_v - elev_u)
        weight_u_v = u_to_v_energy["duration_minutes"] + 3.0 * max(0.0, u_to_v_energy["energy_kwh"])
        g.add_edge(u, v, distance=dist, speed=speed, elevation_delta=(elev_v - elev_u),
                   energy=u_to_v_energy["energy_kwh"], duration=u_to_v_energy["duration_minutes"], weight=weight_u_v)
        
        # Segment energy attributes (V to U)
        v_to_u_energy = ev_model.calculate_energy_consumption(dist, speed, elev_u - elev_v)
        weight_v_u = v_to_u_energy["duration_minutes"] + 3.0 * max(0.0, v_to_u_energy["energy_kwh"])
        g.add_edge(v, u, distance=dist, speed=speed, elevation_delta=(elev_u - elev_v),
                   energy=v_to_u_energy["energy_kwh"], duration=v_to_u_energy["duration_minutes"], weight=weight_v_u)
                   
    return g

def find_nearest_charger(current_node: str, graph: nx.DiGraph) -> str:
    """Helper to locate the nearest spatial node of type 'station' in the driving network."""
    shortest_dist = float("inf")
    closest_charger = ""
    for node, data in graph.nodes(data=True):
        if data.get("type") == "station":
            try:
                # Find path distance
                dist = nx.shortest_path_length(graph, source=current_node, target=node, weight="distance")
                if dist < shortest_dist:
                    shortest_dist = dist
                    closest_charger = node
            except nx.NetworkXNoPath:
                continue
    return closest_charger

def compute_route(
    origin: str,
    destination: str,
    start_soc: float = 100.0,
    ev_model: EVEnergyModel = default_ev_model
) -> Dict[str, Any]:
    """
    Plans an optimal, topography-aware path from origin to destination. 
    Intercepts and injects high-speed charging stops dynamically if battery depletes below 12%.
    """
    graph = build_road_network(ev_model)
    
    if origin not in graph or destination not in graph:
        raise ValueError("Origin or Destination node is outside the SF road network coverage.")

    # Step 1: Attempt direct pathfinding
    try:
        nodes_path = nx.shortest_path(graph, source=origin, target=destination, weight="weight")
    except nx.NetworkXNoPath:
        return {"error": "No viable path found between locations."}

    # Step 2: Validate battery health along the planned route
    current_soc = start_soc
    telemetry = []
    charger_needed = False
    depletion_node = ""
    
    # Log starting node
    telemetry.append({
        "node": nodes_path[0],
        "lat": graph.nodes[nodes_path[0]]["lat"],
        "lng": graph.nodes[nodes_path[0]]["lng"],
        "elev": graph.nodes[nodes_path[0]]["elev"],
        "soc": round(current_soc, 1),
        "energy_consumed_kwh": 0.0,
        "segment_duration_mins": 0.0
    })

    # Traverse segments
    for i in range(len(nodes_path) - 1):
        u = nodes_path[i]
        v = nodes_path[i + 1]
        edge_data = graph[u][v]
        
        # Subtract energy
        energy_kwh = edge_data["energy"]
        soc_loss = (energy_kwh / ev_model.capacity) * 100.0
        current_soc -= soc_loss
        
        # Bound SoC
        current_soc = min(max(current_soc, 0.0), 100.0)
        
        telemetry.append({
            "node": v,
            "lat": graph.nodes[v]["lat"],
            "lng": graph.nodes[v]["lng"],
            "elev": graph.nodes[v]["elev"],
            "soc": round(current_soc, 1),
            "energy_consumed_kwh": round(energy_kwh, 2),
            "segment_duration_mins": round(edge_data["duration"], 1)
        })

        # Trigger Emergency Low-Battery Warning
        if current_soc < 12.0 and i < len(nodes_path) - 2:
            charger_needed = True
            depletion_node = u  # Divert from the last safe node
            break

    # Step 3: Execute Emergency Fallback Reroute if battery depletes
    if charger_needed:
        # Find closest charger from depletion node
        charger_node = find_nearest_charger(depletion_node, graph)
        if not charger_node:
            return {"error": "Battery will deplete and no charging stations are reachable!"}

        # Sub-route A: Origin to Charging Station
        nodes_a = nx.shortest_path(graph, source=origin, target=charger_node, weight="weight")
        
        # Sub-route B: Charging Station to Destination (Assume charging to 85% at station)
        nodes_b = nx.shortest_path(graph, source=charger_node, target=destination, weight="weight")
        
        # Combine paths (removing duplicate connector node)
        combined_nodes = nodes_a + nodes_b[1:]
        
        # Re-calculate absolute telemetry for combined path
        current_soc = start_soc
        telemetry = []
        total_distance = 0.0
        total_duration = 0.0
        
        # Start node
        telemetry.append({
            "node": combined_nodes[0],
            "lat": graph.nodes[combined_nodes[0]]["lat"],
            "lng": graph.nodes[combined_nodes[0]]["lng"],
            "elev": graph.nodes[combined_nodes[0]]["elev"],
            "soc": round(current_soc, 1),
            "charging_stop": False,
            "segment_duration_mins": 0.0
        })

        for i in range(len(combined_nodes) - 1):
            u = combined_nodes[i]
            v = combined_nodes[i + 1]
            edge_data = graph[u][v]
            
            # Distance/Time totals
            total_distance += edge_data["distance"]
            total_duration += edge_data["duration"]

            # SoC depletion
            energy_kwh = edge_data["energy"]
            soc_loss = (energy_kwh / ev_model.capacity) * 100.0
            current_soc -= soc_loss
            current_soc = min(max(current_soc, 0.0), 100.0)
            
            is_charging = False
            # Check if this node is our charging stop, and perform recharge
            if v == charger_node and i < len(combined_nodes) - 2:
                # Add 30 minutes charging duration overhead
                total_duration += 30.0
                current_soc = 85.0  # Charges battery to 85%
                is_charging = True
                
            telemetry.append({
                "node": v,
                "lat": graph.nodes[v]["lat"],
                "lng": graph.nodes[v]["lng"],
                "elev": graph.nodes[v]["elev"],
                "soc": round(current_soc, 1),
                "charging_stop": is_charging,
                "segment_duration_mins": round(edge_data["duration"], 1)
            })

        return {
            "rerouted": True,
            "charging_station_stop": charger_node,
            "total_distance_km": round(total_distance, 2),
            "total_duration_mins": round(total_duration, 1),
            "start_soc": start_soc,
            "final_soc": round(current_soc, 1),
            "nodes": combined_nodes,
            "telemetry": telemetry
        }

    # Otherwise return successful direct path totals
    total_distance = sum(graph[nodes_path[j]][nodes_path[j+1]]["distance"] for j in range(len(nodes_path)-1))
    total_duration = sum(graph[nodes_path[j]][nodes_path[j+1]]["duration"] for j in range(len(nodes_path)-1))
    
    return {
        "rerouted": False,
        "total_distance_km": round(total_distance, 2),
        "total_duration_mins": round(total_duration, 1),
        "start_soc": start_soc,
        "final_soc": round(current_soc, 1),
        "nodes": nodes_path,
        "telemetry": telemetry
    }
