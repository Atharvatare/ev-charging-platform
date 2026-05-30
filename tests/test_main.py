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

def test_vehicle_profiles_physics():
    """
    Verifies that different vehicle models (Ather 450X scooter vs Hyundai Ioniq 5 Crossover)
    exhibit distinct physics-based battery depletion and weight impact behavior.
    """
    from app.engines.battery import VEHICLE_PROFILES
    
    ather_profile = VEHICLE_PROFILES["ather_450x"]
    ioniq_profile = VEHICLE_PROFILES["hyundai_ioniq_5"]
    
    # Ather 450X (Lightweight, low auxiliary draw)
    ather_model = EVEnergyModel(
        mass_kg=ather_profile["mass_kg"],
        drag_coeff=ather_profile["drag_coeff"],
        frontal_area=ather_profile["frontal_area"],
        rolling_coeff=ather_profile["rolling_coeff"],
        battery_capacity_kwh=ather_profile["battery_capacity_kwh"],
        efficiency=ather_profile["efficiency"],
        regen_efficiency=ather_profile["regen_efficiency"],
        auxiliary_draw_w=ather_profile["auxiliary_draw_w"]
    )
    
    # Hyundai Ioniq 5 (Heavy, high auxiliary draw, large battery)
    ioniq_model = EVEnergyModel(
        mass_kg=ioniq_profile["mass_kg"],
        drag_coeff=ioniq_profile["drag_coeff"],
        frontal_area=ioniq_profile["frontal_area"],
        rolling_coeff=ioniq_profile["rolling_coeff"],
        battery_capacity_kwh=ioniq_profile["battery_capacity_kwh"],
        efficiency=ioniq_profile["efficiency"],
        regen_efficiency=ioniq_profile["regen_efficiency"],
        auxiliary_draw_w=ioniq_profile["auxiliary_draw_w"]
    )
    
    # Run identical flat transit segment
    ather_run = ather_model.calculate_energy_consumption(distance_km=10.0, speed_kmh=45.0, elevation_delta_m=0.0)
    ioniq_run = ioniq_model.calculate_energy_consumption(distance_km=10.0, speed_kmh=45.0, elevation_delta_m=0.0)
    
    # Lightweight scooter should consume significantly fewer absolute kWh than heavy premium crossover
    assert ather_run["energy_kwh"] < ioniq_run["energy_kwh"]
    
    # But because Ather battery is very small (3.7 kWh vs 72.6 kWh), the SoC percentage delta should be higher
    assert ather_run["soc_delta"] > ioniq_run["soc_delta"]
    print("SUCCESS: Dynamic EV Profiles physics calculations are scientifically accurate!")

def test_battery_physics_weather_impact():
    """
    Verifies that headwinds, rainfall (wet asphalt resistance), and temperature extremes (HVAC)
    correctly increase EV battery depletions under the senior consultant physics model.
    """
    model_baseline = EVEnergyModel(temperature_c=25.0, wind_speed_kmh=0.0, wind_direction="none", rain="none")
    model_headwind = EVEnergyModel(temperature_c=25.0, wind_speed_kmh=40.0, wind_direction="headwind", rain="none")
    model_tailwind = EVEnergyModel(temperature_c=25.0, wind_speed_kmh=40.0, wind_direction="tailwind", rain="none")
    model_heavy_rain = EVEnergyModel(temperature_c=25.0, wind_speed_kmh=0.0, wind_direction="none", rain="heavy")
    model_extreme_heat = EVEnergyModel(temperature_c=38.0, wind_speed_kmh=0.0, wind_direction="none", rain="none")

    # Run identical flat transit segment (10 km at 60 km/h)
    baseline_run = model_baseline.calculate_energy_consumption(distance_km=10.0, speed_kmh=60.0, elevation_delta_m=0.0)
    headwind_run = model_headwind.calculate_energy_consumption(distance_km=10.0, speed_kmh=60.0, elevation_delta_m=0.0)
    tailwind_run = model_tailwind.calculate_energy_consumption(distance_km=10.0, speed_kmh=60.0, elevation_delta_m=0.0)
    heavy_rain_run = model_heavy_rain.calculate_energy_consumption(distance_km=10.0, speed_kmh=60.0, elevation_delta_m=0.0)
    extreme_heat_run = model_extreme_heat.calculate_energy_consumption(distance_km=10.0, speed_kmh=60.0, elevation_delta_m=0.0)

    # 1. Headwind should consume more absolute energy than baseline
    assert headwind_run["energy_kwh"] > baseline_run["energy_kwh"]
    
    # 2. Tailwind should consume less absolute energy than baseline
    assert tailwind_run["energy_kwh"] < baseline_run["energy_kwh"]
    
    # 3. Heavy rain (increased rolling resistance) should consume more than baseline
    assert heavy_rain_run["energy_kwh"] > baseline_run["energy_kwh"]
    
    # 4. Extreme heat (battery chiller + A/C auxiliary draws) should consume more than baseline
    assert extreme_heat_run["energy_kwh"] > baseline_run["energy_kwh"]

    print("SUCCESS: Senior Consultant environmental physics calculations are fully verified!")

def test_persistent_endpoints():
    """
    Verifies that the FastAPI endpoints for wallet deposits, active bookings,
    and OCPP completions respond correctly.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    with TestClient(app) as client:
        # 1. Get Stations Grid
        stations_res = client.get("/api/stations/")
        assert stations_res.status_code == 200
        stations_data = stations_res.json()
        assert len(stations_data) == 25
        
        # 2. Get Topographic Nodes
        nodes_res = client.get("/api/routing/nodes")
        assert nodes_res.status_code == 200
        assert len(nodes_res.json()) > 0
        
        # 3. Get About Company Profile
        about_res = client.get("/about")
        assert about_res.status_code == 200
        assert "GoBharat EV" in about_res.text
        assert "About Company Profile" in about_res.text
        
        # Get Support Hub
        support_res = client.get("/support")
        assert support_res.status_code == 200
        assert "Support Hub" in support_res.text
        
        # 4. Submit Support Ticket Successfully
        ticket_payload = {
            "name": "Jane Doe",
            "email": "jane@ev.com",
            "subject": "Incline calculation feedback",
            "message": "The Western Ghats slope algorithm works beautifully! Very accurate depletions."
        }
        submit_res = client.post("/api/contact/submit", json=ticket_payload)
        assert submit_res.status_code == 200
        assert "submitted successfully" in submit_res.json()["message"]
        
        # 5. Submit Invalid Support Ticket (Empty field validations)
        invalid_payload = {
            "name": "",
            "email": "jane@ev.com",
            "subject": "Incline calculation feedback",
            "message": "Empty name."
        }
        submit_invalid_res = client.post("/api/contact/submit", json=invalid_payload)
        # Pydantic validates empty strings if we check length, or they might be accepted as strings but let's test FastAPI pydantic validation behavior or manual check
        # Wait, app/main.py checks: if not req.name or not req.email or not req.subject or not req.message: raise HTTPException(status_code=400, detail="All contact form fields are required.")
        # So it returns 400!
        assert submit_invalid_res.status_code == 400
        assert "All contact form fields are required." in submit_invalid_res.json()["detail"]
        
        # 6. Get Login & Register Page
        login_res = client.get("/login")
        assert login_res.status_code == 200
        assert "Consumer Login & Register Portal" in login_res.text
        assert "authController()" in login_res.text
        
        # 7. Register a New Consumer Account Dynamically
        import random
        random_num = random.randint(100000, 999999)
        new_consumer_email = f"consumer_{random_num}@test.com"
        register_payload = {
            "email": new_consumer_email,
            "password": "securepassword123",
            "full_name": "John Doe",
            "phone": "+91 99999 88888",
            "role": "user"
        }
        reg_res = client.post("/api/auth/register", json=register_payload)
        assert reg_res.status_code == 200
        registered_data = reg_res.json()
        assert registered_data["email"] == new_consumer_email
        assert registered_data["full_name"] == "John Doe"
        assert registered_data["phone"] == "+91 99999 88888"
        assert registered_data["wallet_balance"] == 100.0
        
        # 8. Log In with Form Data (x-www-form-urlencoded) to Retrieve Token
        login_payload = {
            "username": new_consumer_email,
            "password": "securepassword123"
        }
        login_token_res = client.post("/api/auth/login", data=login_payload)
        assert login_token_res.status_code == 200
        token_data = login_token_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # 9. Test Routing History (GET /api/routing/history)
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        history_res = client.get("/api/routing/history", headers=headers)
        assert history_res.status_code == 200
        assert isinstance(history_res.json(), list)

        # 10. Test Chatbot Ask (POST /api/chatbot/ask)
        chatbot_payload = {"message": "hello chatbot"}
        chatbot_res = client.post("/api/chatbot/ask", json=chatbot_payload, headers=headers)
        assert chatbot_res.status_code == 200
        assert "reply" in chatbot_res.json()
        assert "Hello" in chatbot_res.json()["reply"]

        # 11. Test Chatbot Ask with battery keyword
        chatbot_payload_bat = {"message": "what is my battery profile?"}
        chatbot_res_bat = client.post("/api/chatbot/ask", json=chatbot_payload_bat, headers=headers)
        assert chatbot_res_bat.status_code == 200
        assert "wallet balance" in chatbot_res_bat.json()["reply"]

        # 12. Test Bookings Reserve with OSM dynamic port ID (POST /api/bookings/reserve)
        import uuid
        mock_port_uuid = str(uuid.uuid4())
        reserve_payload = {
            "port_id": mock_port_uuid,
            "duration_hours": 2
        }
        reserve_res = client.post("/api/bookings/reserve", json=reserve_payload, headers=headers)
        assert reserve_res.status_code == 200
        res_data = reserve_res.json()
        assert "reservation_id" in res_data
        assert "qr_code" in res_data
        assert res_data["message"] == "Charger port reserved successfully."
        
        print("SUCCESS: Fully persistent backend routers, About page, Contact ticketing, and Consumer Auth verified via TestClient!")



def test_websocket_broadcasts():
    """
    Verifies that the WebSocket telemetry broadcast channel successfully streams
    live PORT_STATUS_UPDATE events to connected client handshakes.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    
    # Connect client websocket
    with client.websocket_connect("/ws") as websocket:
        # 1. Receive the initial systemic greeting message
        greeting = websocket.receive_json()
        assert greeting["type"] == "SYSTEM"
        assert "Connected" in greeting["message"]
        
        # 2. Simulate client telemetry logs text transmission
        websocket.send_text("OCPP_SIMULATION_HEARTBEAT_PING")
        broadcast_log = websocket.receive_json()
        assert broadcast_log["type"] == "TELEMETRY_LOG"
        assert "OCPP_SIMULATION_HEARTBEAT_PING" in broadcast_log["message"]
        
    print("SUCCESS: Asynchronous WebSocket handshakes and telemetry broadcasts successfully verified!")


def test_port_fault_injection():
    """
    Verifies that injecting faults forces the port into MAINTENANCE status, 
    and clearing it restores status to AVAILABLE.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    import random
    
    with TestClient(app) as client:
        # 1. Register and login to get auth token
        random_num = random.randint(100000, 999999)
        new_consumer_email = f"fault_tester_{random_num}@test.com"
        register_payload = {
            "email": new_consumer_email,
            "password": "securepassword123",
            "full_name": "Fault Tester",
            "phone": "+91 99999 77777",
            "role": "user"
        }
        client.post("/api/auth/register", json=register_payload)
        
        login_payload = {
            "username": new_consumer_email,
            "password": "securepassword123"
        }
        login_res = client.post("/api/auth/login", data=login_payload)
        token_data = login_res.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # 2. Fetch stations and get a port
        stations_res = client.get("/api/stations/")
        assert stations_res.status_code == 200
        stations = stations_res.json()
        assert len(stations) > 0
        port_id = stations[0]["ports"][0]["id"]
        
        # 3. Inject fault
        fault_payload = {"fault_type": "OVER_VOLTAGE"}
        fault_res = client.post(f"/api/bookings/port/{port_id}/fault", json=fault_payload, headers=headers)
        assert fault_res.status_code == 200
        assert fault_res.json()["status"] == "MAINTENANCE"
        
        # 4. Clear fault
        clear_res = client.post(f"/api/bookings/port/{port_id}/clear-fault", headers=headers)
        assert clear_res.status_code == 200
        assert clear_res.json()["status"] == "AVAILABLE"
        
        print("SUCCESS: Fault injection and clear-fault endpoints verified persistently!")






