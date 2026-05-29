import random
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.station import Station, Port, SolarInsight

# High-fidelity charging station profiles centered around Mumbai and Lonavala
SEED_STATIONS = [
    {
        "name": "Jio-bp Pulse - BKC Hub",
        "address": "G Block BKC, Bandra Kurla Complex, Mumbai, MH 400051",
        "lat": 19.0600,
        "lng": 72.8600,
        "rating": 4.9,
        "solar": {"output": 45.5, "storage": 120.0, "score": 92},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "OCCUPIED"},
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "CHARGING"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power EZ Charge - Bandra Reclamation",
        "address": "KC Marg, Bandra West, Mumbai, MH 400050",
        "lat": 19.0430,
        "lng": 72.8340,
        "rating": 4.7,
        "solar": {"output": 25.0, "storage": 80.0, "score": 85},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 19.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 19.0, "status": "OCCUPIED"},
            {"connector": "CHAdeMO", "power": 50.0, "price": 15.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Magenta ChargeGrid - Lower Parel",
        "address": "Senapati Bapat Marg, Lower Parel, Mumbai, MH 400013",
        "lat": 18.9950,
        "lng": 72.8300,
        "rating": 4.8,
        "solar": {"output": 60.0, "storage": 200.0, "score": 98},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Ather Grid - Powai Tech Park",
        "address": "Central Ave, Hiranandani Gardens, Powai, Mumbai, MH 400076",
        "lat": 19.1300,
        "lng": 72.9100,
        "rating": 4.4,
        "solar": {"output": 12.0, "storage": 40.0, "score": 72},
        "ports": [
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "OCCUPIED"},
            {"connector": "CHAdeMO", "power": 50.0, "price": 14.5, "status": "MAINTENANCE"}
        ]
    },
    {
        "name": "Tata Power EZ Charge - Navi Mumbai Vashi",
        "address": "Vashi Rd, Sector 17, Vashi, Navi Mumbai, MH 400703",
        "lat": 19.0650,
        "lng": 73.0000,
        "rating": 4.5,
        "solar": {"output": 35.0, "storage": 100.0, "score": 88},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 19.5, "status": "AVAILABLE"},
            {"connector": "CHAdeMO", "power": 100.0, "price": 16.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Magenta ChargeGrid - Lonavala Hill Station",
        "address": "Mumbai-Pune Expressway Food Plaza, Lonavala, MH 410401",
        "lat": 18.7500,
        "lng": 73.4000,
        "rating": 4.6,
        "solar": {"output": 75.0, "storage": 250.0, "score": 100},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 20.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 13.0, "status": "AVAILABLE"}
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
