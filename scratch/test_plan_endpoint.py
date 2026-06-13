import os
from fastapi.testclient import TestClient

# Use isolated test database
os.environ["DATABASE_URL"] = "sqlite:///test_ev_charging.db"
if os.path.exists("test_ev_charging.db"):
    try:
        os.remove("test_ev_charging.db")
    except Exception:
        pass

from app.core.database import init_db
from app.core.seed import seed_database
init_db()
seed_database()

from app.main import app

client = TestClient(app)

# Register user
register_payload = {
    "email": "testplan@ev.com",
    "password": "securepassword123",
    "full_name": "Test Plan User",
    "phone": "9999999999",
    "role": "user"
}
reg_res = client.post("/api/auth/register", json=register_payload)
print("Register Status:", reg_res.status_code)

# Login
login_payload = {
    "username": "testplan@ev.com",
    "password": "securepassword123"
}
login_res = client.post("/api/auth/login", data=login_payload)
print("Login Status:", login_res.status_code)
token = login_res.json()["access_token"]

# Test plan route
headers = {"Authorization": f"Bearer {token}"}
plan_payload = {
    "origin": "Lower_Parel",
    "destination": "Lonavala_Expressway_Stop",
    "start_soc": 100,
    "vehicle": "tata_nexon_ev_max",
    "temperature_c": 25.0,
    "wind_speed_kmh": 0.0,
    "wind_direction": "none",
    "rain": "none"
}
plan_res = client.post("/api/routing/plan", json=plan_payload, headers=headers)
print("Plan Status Code:", plan_res.status_code)
print("Plan Response:", plan_res.text)
