import random
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.station import Station, Port, SolarInsight

# High-fidelity charging station profiles centered around San Francisco (37.7749, -122.4194)
SEED_STATIONS = [
    {
        "name": "Tesla Supercharger - Rincon Center",
        "address": "121 Spear St, San Francisco, CA 94105",
        "lat": 37.7915,
        "lng": -122.3923,
        "rating": 4.9,
        "solar": {"output": 45.5, "storage": 120.0, "score": 92},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 0.42, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 250.0, "price": 0.42, "status": "OCCUPIED"},
            {"connector": "CCS2", "power": 250.0, "price": 0.42, "status": "CHARGING"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 0.28, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Electrify America - Union Square",
        "address": "325 Mason St, San Francisco, CA 94102",
        "lat": 37.7865,
        "lng": -122.4098,
        "rating": 4.7,
        "solar": {"output": 25.0, "storage": 80.0, "score": 85},
        "ports": [
            {"connector": "CCS2", "power": 350.0, "price": 0.48, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 0.38, "status": "OCCUPIED"},
            {"connector": "CHAdeMO", "power": 100.0, "price": 0.35, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Rivian Waypoint - Salesforce Transit Center",
        "address": "425 Mission St, San Francisco, CA 94105",
        "lat": 37.7892,
        "lng": -122.3970,
        "rating": 4.8,
        "solar": {"output": 60.0, "storage": 200.0, "score": 98},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 0.39, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 0.39, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 0.25, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "ChargePoint Hub - Civic Center",
        "address": "355 McAllister St, San Francisco, CA 94102",
        "lat": 37.7798,
        "lng": -122.4178,
        "rating": 4.4,
        "solar": {"output": 12.0, "storage": 40.0, "score": 72},
        "ports": [
            {"connector": "Type 2 AC", "power": 22.0, "price": 0.24, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 0.24, "status": "OCCUPIED"},
            {"connector": "CHAdeMO", "power": 50.0, "price": 0.30, "status": "MAINTENANCE"}
        ]
    },
    {
        "name": "EVgo Station - Mission District",
        "address": "2351 Mission St, San Francisco, CA 94110",
        "lat": 37.7554,
        "lng": -122.4190,
        "rating": 4.5,
        "solar": {"output": 35.0, "storage": 100.0, "score": 88},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 0.40, "status": "AVAILABLE"},
            {"connector": "CHAdeMO", "power": 100.0, "price": 0.36, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "GreenGrid - Golden Gate Park",
        "address": "50 Hagiwara Tea Garden Dr, San Francisco, CA 94118",
        "lat": 37.7702,
        "lng": -122.4702,
        "rating": 4.6,
        "solar": {"output": 75.0, "storage": 250.0, "score": 100},  # 100% green solar
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 0.35, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 0.22, "status": "AVAILABLE"}
        ]
    }
]

def seed_database():
    """Seeds the database with users and spatial charging stations if empty."""
    with Session(engine) as session:
        # 1. Seed Users
        existing_user = session.exec(select(User).where(User.email == "user@ev.com")).first()
        if not existing_user:
            user = User(
                email="user@ev.com",
                hashed_password=get_password_hash("password123"),
                full_name="Alex Mercer",
                role="user",
                wallet_balance=150.00
            )
            session.add(user)
            print("Seeded User: user@ev.com (password123)")

        existing_admin = session.exec(select(User).where(User.email == "admin@ev.com")).first()
        if not existing_admin:
            admin = User(
                email="admin@ev.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Director Admin",
                role="admin",
                wallet_balance=500.00
            )
            session.add(admin)
            print("Seeded Admin: admin@ev.com (admin123)")

        # 2. Seed Stations, Ports, & Solar
        existing_station = session.exec(select(Station)).first()
        if not existing_station:
            for st_data in SEED_STATIONS:
                station = Station(
                    name=st_data["name"],
                    address=st_data["address"],
                    latitude=st_data["lat"],
                    longitude=st_data["lng"],
                    rating=st_data["rating"]
                )
                session.add(station)
                session.commit()  # Commit so we get the UUID index
                session.refresh(station)

                # Seed solar telemetry
                solar = SolarInsight(
                    station_id=station.id,
                    solar_output_kw=st_data["solar"]["output"],
                    battery_storage_kwh=st_data["solar"]["storage"],
                    renewable_percentage=st_data["solar"]["score"]
                )
                session.add(solar)

                # Seed charging sockets (ports)
                for port_data in st_data["ports"]:
                    port = Port(
                        station_id=station.id,
                        connector_type=port_data["connector"],
                        power_kw=port_data["power"],
                        price_per_kwh=port_data["price"],
                        status=port_data["status"]
                    )
                    session.add(port)
            session.commit()
            print("Seeded 6 high-fidelity EV Charging Stations with multi-ports & solar analytics!")
        else:
            print("Database already contains stations. Skipping spatial seed.")

if __name__ == "__main__":
    seed_database()
