import pytest
from app.engines.battery import EVEnergyModel
from app.engines.router import compute_route
from app.engines.queue_predictor import forecast_station_queue

def test_battery_physics_climb():
    """
    Verifies that driving up a steep hill drains more battery 
    than standard flat driving.
    """
    model = EVEnergyModel()
    
    # Flat driving segment
    flat_data = model.calculate_energy_consumption(
        distance_km=2.0,
        speed_kmh=50.0,
        elevation_delta_m=0.0
    )
    
    # Steep climb segment (2.0 km distance, 120m elevation climb)
    climb_data = model.calculate_energy_consumption(
        distance_km=2.0,
        speed_kmh=50.0,
        elevation_delta_m=120.0
    )
    
    assert climb_data["energy_kwh"] > flat_data["energy_kwh"]
    assert climb_data["soc_delta"] > flat_data["soc_delta"]
    print("SUCCESS: Physics Engine correctly charges more energy for hill climbs.")

def test_battery_physics_regen():
    """
    Verifies that driving down a steep decline triggers regenerative braking 
    and recaptures positive energy back to the battery (negative energy delta).
    """
    model = EVEnergyModel()
    
    # Steep decline segment (2.0 km distance, 180m descent)
    decline_data = model.calculate_energy_consumption(
        distance_km=2.0,
        speed_kmh=40.0,
        elevation_delta_m=-180.0
    )
    
    # Regenerative braking should recapture energy, leading to a negative energy draw
    assert decline_data["regenerative_kwh"] > 0.0
    print(f"SUCCESS: Regenerative braking recaptured: {decline_data['regenerative_kwh']} kWh.")

def test_router_solver_direct():
    """
    Asserts that the NetworkX Dijkstra router plans valid path coordinate chains 
    between Mumbai junctions.
    """
    # Plan route from Lower Parel to BKC Hub
    res = compute_route(origin="Lower_Parel", destination="BKC_Hub", start_soc=90.0)
    
    assert "error" not in res
    assert res["rerouted"] is False
    assert len(res["nodes"]) >= 2
    assert res["nodes"][0] == "Lower_Parel"
    assert res["nodes"][-1] == "BKC_Hub"
    assert res["final_soc"] < 90.0  # Consumed battery
    print("SUCCESS: Router computed valid direct route nodes.")

def test_router_low_battery_reroute():
    """
    Asserts that the Emergency Low-Battery fallback system automatically intercepts 
    route calculation when the vehicle start SoC is critically low (e.g. 11% SoC) 
    and injects a charging stop.
    """
    # Plan long steep route with starting SoC of only 11% (e.g. Gateway of India to Lonavala)
    res = compute_route(origin="Gateway_of_India", destination="Lonavala_Expressway_Stop", start_soc=11.0)
    
    assert "error" not in res
    assert res["rerouted"] is True
    assert "charging_station_stop" in res
    # Arrival battery should be higher because the vehicle recharged to 85% at the stop
    assert res["final_soc"] > 11.0  
    print(f"SUCCESS: Emergency mode successfully injected charging stop at: {res['charging_station_stop']}.")

def test_queue_forecaster_rush_hour():
    """
    Verifies that wait times are elevated during peak morning commute periods.
    """
    # Off-peak hours
    off_peak = forecast_station_queue(total_ports=4, occupied_ports=4, hour_of_day=14)
    
    # Peak rush hour (8 AM)
    peak = forecast_station_queue(total_ports=4, occupied_ports=4, hour_of_day=8)
    
    assert peak["predicted_wait_minutes"] > off_peak["predicted_wait_minutes"]
    assert peak["demand_status"] == "CRITICAL"
    print("SUCCESS: Queue forecaster calculated peak wait time coefficients.")
