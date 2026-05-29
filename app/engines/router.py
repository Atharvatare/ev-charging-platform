import networkx as nx
from typing import Dict, Any, List, Tuple
from app.engines.battery import EVEnergyModel, default_ev_model

# Definition of nodes in the Mumbai-Pune road network with latitude, longitude, and elevation
SF_GRAPH_NODES = {
    "Gateway_of_India": {"lat": 18.9220, "lng": 72.8347, "elev": 2.0, "type": "road"},
    "Lower_Parel": {"lat": 18.9950, "lng": 72.8300, "elev": 6.0, "type": "road"},
    "BKC_Hub": {"lat": 19.0600, "lng": 72.8600, "elev": 4.0, "type": "station"},
    "Bandra_Reclamation": {"lat": 19.0430, "lng": 72.8340, "elev": 5.0, "type": "station"},
    "Andheri_West": {"lat": 19.1200, "lng": 72.8300, "elev": 10.0, "type": "road"},
    "Powai_Lake": {"lat": 19.1300, "lng": 72.9100, "elev": 25.0, "type": "station"},
    "Navi_Mumbai_Vashi": {"lat": 19.0650, "lng": 73.0000, "elev": 8.0, "type": "station"},
    "Chembur_Junction": {"lat": 19.0600, "lng": 72.9000, "elev": 9.0, "type": "road"},
    "Lonavala_Expressway_Stop": {"lat": 18.7500, "lng": 73.4000, "elev": 620.0, "type": "station"},
    "Pune_Aundh": {"lat": 18.5600, "lng": 73.8000, "elev": 560.0, "type": "road"},
    "Expressway_Toll_East": {"lat": 18.8000, "lng": 73.3000, "elev": 420.0, "type": "road"},
    "Expressway_Toll_West": {"lat": 18.9000, "lng": 73.1500, "elev": 120.0, "type": "road"}
}

# Driving connections (edges) with physical distances (km) and base limits (km/h)
SF_GRAPH_EDGES = [
    # Mumbai Suburban grid
    ("Gateway_of_India", "Lower_Parel", 9.5, 45),
    ("Lower_Parel", "BKC_Hub", 8.2, 50),
    ("Lower_Parel", "Bandra_Reclamation", 6.8, 50),
    ("Bandra_Reclamation", "BKC_Hub", 4.5, 40),
    ("Bandra_Reclamation", "Andheri_West", 11.2, 50),
    
    # Suburbs to Highway entry
    ("Andheri_West", "Powai_Lake", 9.8, 40),
    ("BKC_Hub", "Chembur_Junction", 6.5, 45),
    ("Chembur_Junction", "Navi_Mumbai_Vashi", 12.4, 60),
    ("Powai_Lake", "Chembur_Junction", 7.8, 40),
    
    # Mumbai-Pune Expressway segments (topography-heavy!)
    ("Navi_Mumbai_Vashi", "Expressway_Toll_West", 22.5, 80),
    ("Expressway_Toll_West", "Expressway_Toll_East", 18.2, 80),
    ("Expressway_Toll_East", "Lonavala_Expressway_Stop", 12.8, 70),  # Steep climb to Lonavala (420m to 620m)
    ("Lonavala_Expressway_Stop", "Pune_Aundh", 55.4, 90)              # Expressway terminal run to Pune
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
        total_distance = 0.0
        total_duration = 0.0
        
        # Check if the starting node itself is the charging stop
        start_is_charger = (combined_nodes[0] == charger_node)
        if start_is_charger:
            current_soc = 85.0
            total_duration += 30.0
            
        telemetry = []
        # Start node
        telemetry.append({
            "node": combined_nodes[0],
            "lat": graph.nodes[combined_nodes[0]]["lat"],
            "lng": graph.nodes[combined_nodes[0]]["lng"],
            "elev": graph.nodes[combined_nodes[0]]["elev"],
            "soc": round(current_soc, 1),
            "charging_stop": start_is_charger,
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
