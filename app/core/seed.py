import random
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.station import Station, Port, SolarInsight

# High-fidelity nationwide charging station profiles centered across major states in India (25 stations)
SEED_STATIONS = [
    # --- MAHARASHTRA (Nagpur / Mumbai / Pune / Highway) ---
    {
        "name": "GoBharat EV Flagship Command Hub",
        "address": "Kalmeshwar Town Center, Nagpur, Maharashtra 441501",
        "lat": 21.2333,
        "lng": 78.9167,
        "rating": 5.0,
        "solar": {"output": 80.0, "storage": 300.0, "score": 100},
        "ports": [
            {"connector": "CCS2", "power": 350.0, "price": 15.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 12.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 8.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Jio-bp Pulse - BKC Hub",
        "address": "G Block BKC, Bandra Kurla Complex, Mumbai, Maharashtra 400051",
        "lat": 19.0600,
        "lng": 72.8600,
        "rating": 4.9,
        "solar": {"output": 45.5, "storage": 120.0, "score": 92},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 16.0, "status": "OCCUPIED"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power EZ Charge - Bandra Reclamation",
        "address": "Bandra Reclamation Flyover, Bandra West, Mumbai, Maharashtra 400050",
        "lat": 19.0430,
        "lng": 72.8340,
        "rating": 4.8,
        "solar": {"output": 55.0, "storage": 150.0, "score": 96},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 17.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Zeon Charging - Hinjawadi IT Park",
        "address": "Phase 1 Hinjawadi Info Tech Park, Pune, Maharashtra 411057",
        "lat": 18.5913,
        "lng": 73.7386,
        "rating": 4.7,
        "solar": {"output": 35.0, "storage": 90.0, "score": 88},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 50.0, "price": 14.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "KSEB Charge - Lonavala Expressway Stop",
        "address": "Mumbai-Pune Expressway Toll Stop, Lonavala, Maharashtra 410401",
        "lat": 18.7500,
        "lng": 73.4000,
        "rating": 4.6,
        "solar": {"output": 60.0, "storage": 200.0, "score": 95},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 19.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.5, "status": "AVAILABLE"}
        ]
    },
    # --- DELHI NCR ---
    {
        "name": "EESL Supercharger - Connaught Place",
        "address": "Radial Road 1, Connaught Place, New Delhi, Delhi 110001",
        "lat": 28.6304,
        "lng": 77.2177,
        "rating": 4.7,
        "solar": {"output": 25.0, "storage": 80.0, "score": 85},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 19.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 150.0, "price": 19.0, "status": "OCCUPIED"}
        ]
    },
    {
        "name": "Fortum Charge - Gurgaon Cyber City",
        "address": "DLF Cyber City Phase 2, Gurugram, Haryana 122002",
        "lat": 28.4950,
        "lng": 77.0878,
        "rating": 4.8,
        "solar": {"output": 50.0, "storage": 160.0, "score": 94},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Jio-bp Pulse - Noida Sector 62",
        "address": "Block C Sector 62 Industrial Area, Noida, Uttar Pradesh 201301",
        "lat": 28.6223,
        "lng": 77.3588,
        "rating": 4.5,
        "solar": {"output": 30.0, "storage": 100.0, "score": 90},
        "ports": [
            {"connector": "CCS2", "power": 120.0, "price": 16.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 10.5, "status": "AVAILABLE"}
        ]
    },
    # --- KARNATAKA (Bengaluru / Highway) ---
    {
        "name": "Ather Grid Hub - Indiranagar",
        "address": "100 Feet Rd, Indiranagar, Bengaluru, Karnataka 560038",
        "lat": 12.9784,
        "lng": 77.6408,
        "rating": 4.8,
        "solar": {"output": 60.0, "storage": 200.0, "score": 98},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power - Koramangala Grid",
        "address": "80 Feet Road, 4th Block Koramangala, Bengaluru, Karnataka 560034",
        "lat": 12.9352,
        "lng": 77.6244,
        "rating": 4.6,
        "solar": {"output": 40.0, "storage": 130.0, "score": 91},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 17.5, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 50.0, "price": 14.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Ather Grid - Whitefield IT Corridor",
        "address": "ITPB Main Road, Whitefield, Bengaluru, Karnataka 560066",
        "lat": 12.9698,
        "lng": 77.7499,
        "rating": 4.5,
        "solar": {"output": 45.0, "storage": 140.0, "score": 93},
        "ports": [
            {"connector": "CCS2", "power": 120.0, "price": 17.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    # --- TAMIL NADU (Chennai / Highway) ---
    {
        "name": "Zeon Charging - OMR Tech Corridor",
        "address": "Rajiv Gandhi Salai OMR, Adyar, Chennai, Tamil Nadu 600020",
        "lat": 12.9229,
        "lng": 80.2312,
        "rating": 4.7,
        "solar": {"output": 40.0, "storage": 120.0, "score": 90},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power - Adyar Central",
        "address": "Sardar Patel Road, Adyar, Chennai, Tamil Nadu 600020",
        "lat": 13.0063,
        "lng": 80.2574,
        "rating": 4.5,
        "solar": {"output": 35.0, "storage": 100.0, "score": 87},
        "ports": [
            {"connector": "CCS2", "power": 120.0, "price": 17.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Zeon Charging - Krishnagiri Highway Stop",
        "address": "Krishnagiri Highway NH44, Krishnagiri, Tamil Nadu 635001",
        "lat": 12.5265,
        "lng": 78.2140,
        "rating": 4.4,
        "solar": {"output": 12.0, "storage": 40.0, "score": 72},
        "ports": [
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"},
            {"connector": "CCS2", "power": 50.0, "price": 14.5, "status": "AVAILABLE"}
        ]
    },
    # --- TELANGANA ---
    {
        "name": "GMR Pulse - Shamshabad Airport",
        "address": "RGIA Terminal Arrivals Road, Shamshabad, Hyderabad, Telangana 500409",
        "lat": 17.2403,
        "lng": 78.4294,
        "rating": 4.6,
        "solar": {"output": 75.0, "storage": 250.0, "score": 100},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 20.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 13.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Ather Grid - Gachibowli Outer Ring Road",
        "address": "ISB Road, Gachibowli Financial District, Hyderabad, Telangana 500032",
        "lat": 17.4401,
        "lng": 78.3489,
        "rating": 4.8,
        "solar": {"output": 50.0, "storage": 160.0, "score": 95},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    # --- WEST BENGAL ---
    {
        "name": "Bengal EcoCharge - Salt Lake Sector V",
        "address": "GP Block, Sector V, Salt Lake, Kolkata, West Bengal 700091",
        "lat": 22.5726,
        "lng": 88.4339,
        "rating": 4.5,
        "solar": {"output": 35.0, "storage": 100.0, "score": 88},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 19.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power - Eco Park Town",
        "address": "Major Arterial Road, New Town Eco Park, Kolkata, West Bengal 700156",
        "lat": 22.6105,
        "lng": 88.4682,
        "rating": 4.6,
        "solar": {"output": 45.0, "storage": 140.0, "score": 93},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.5, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Fortum Charge - Howrah Junction",
        "address": "Howrah Station Road, Howrah, West Bengal 711101",
        "lat": 22.5855,
        "lng": 88.3414,
        "rating": 4.4,
        "solar": {"output": 20.0, "storage": 60.0, "score": 80},
        "ports": [
            {"connector": "CCS2", "power": 100.0, "price": 17.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    # --- GUJARAT ---
    {
        "name": "Jio-bp Pulse - SG Highway",
        "address": "Sarkhej - Gandhinagar Highway, Bodakdev, Ahmedabad, Gujarat 380054",
        "lat": 23.0225,
        "lng": 72.5714,
        "rating": 4.7,
        "solar": {"output": 40.0, "storage": 120.0, "score": 91},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power - Surat Diamond Bourse",
        "address": "Surat Diamond Bourse Road, Surat, Gujarat 395007",
        "lat": 21.1702,
        "lng": 72.8311,
        "rating": 4.8,
        "solar": {"output": 60.0, "storage": 180.0, "score": 97},
        "ports": [
            {"connector": "CCS2", "power": 250.0, "price": 18.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.0, "status": "AVAILABLE"}
        ]
    },
    # --- KERALA ---
    {
        "name": "KSEB Charge - Kochi Infopark",
        "address": "Infopark Campus Road, Kakkanad, Kochi, Kerala 682030",
        "lat": 9.9816,
        "lng": 76.3276,
        "rating": 4.8,
        "solar": {"output": 50.0, "storage": 150.0, "score": 96},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 17.0, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Fortum Charge - Trivandrum Central",
        "address": "MG Road, Thiruvananthapuram, Kerala 695001",
        "lat": 8.5074,
        "lng": 76.9511,
        "rating": 4.5,
        "solar": {"output": 30.0, "storage": 90.0, "score": 89},
        "ports": [
            {"connector": "CCS2", "power": 120.0, "price": 16.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 10.5, "status": "AVAILABLE"}
        ]
    },
    # --- RAJASTHAN ---
    {
        "name": "Rajasthan EcoPulse - Jaipur Pink City",
        "address": "Tonk Road Near Nehru Garden, Jaipur, Rajasthan 302015",
        "lat": 26.9124,
        "lng": 75.7873,
        "rating": 4.6,
        "solar": {"output": 35.0, "storage": 110.0, "score": 90},
        "ports": [
            {"connector": "CCS2", "power": 150.0, "price": 18.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 12.0, "status": "AVAILABLE"}
        ]
    },
    {
        "name": "Tata Power - Udaipur Highway Stop",
        "address": "NH8 Highway Halt, Udaipur, Rajasthan 313001",
        "lat": 24.5854,
        "lng": 73.7125,
        "rating": 4.5,
        "solar": {"output": 25.0, "storage": 80.0, "score": 83},
        "ports": [
            {"connector": "CCS2", "power": 120.0, "price": 17.5, "status": "AVAILABLE"},
            {"connector": "Type 2 AC", "power": 22.0, "price": 11.0, "status": "AVAILABLE"}
        ]
    }
]

def seed_database(force: bool = False):
    """Seeds the database with users and spatial charging stations, with auto-upgrade support."""
    with Session(engine) as session:
        # Auto-detect old database schema and upgrade to new Pan-India 25-station grid
        existing_stations = session.exec(select(Station)).all()
        has_old_data = False
        if existing_stations:
            # Force upgrade if database has less than 25 stations
            if len(existing_stations) < 25:
                has_old_data = True

        if force or has_old_data:
            print("Auto-upgrading database tables for clean pan-India re-seeding...")
            # Clear solar insights
            for item in session.exec(select(SolarInsight)).all():
                session.delete(item)
            # Clear ports
            for item in session.exec(select(Port)).all():
                session.delete(item)
            # Clear stations
            for item in session.exec(select(Station)).all():
                session.delete(item)
            session.commit()

        # 1. Seed Users
        existing_user = session.exec(select(User).where(User.email == "user@ev.com")).first()
        if not existing_user:
            user = User(
                email="user@ev.com",
                hashed_password=get_password_hash("password123"),
                full_name="Alex Mercer",
                role="user",
                wallet_balance=1000.00
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
            print("Seeded 25 high-fidelity Pan-India EV Charging Stations across multiple states!")
        else:
            print("Database already contains the latest stations. Skipping spatial seed.")

if __name__ == "__main__":
    seed_database()
