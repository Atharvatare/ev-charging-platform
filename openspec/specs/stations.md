# Specification: Charging Stations Database & Seeding

This specification documents the 25 charging stations seeded across India, detailing their address structures, charging sockets, and our new flagship station in Nagpur.

---

## 📍 1. Database Seeding Mechanics
FastAPI boots up database checks on startup (`on_startup` in [`app/main.py`](file:///d:/EV%20CHARGING/app/main.py)). 
1.  **Count Audit**: If database stations count is `< 25`, the core auto-upgrade schema triggers (`seed_database(force=True)` in [`app/core/seed.py`](file:///d:/EV%20CHARGING/app/core/seed.py)).
2.  **Telemetry Cleanup**: Older solar metrics, charging bookings, and ports tables are dropped cleanly before performing a fresh seed.
3.  **Entity Mapping**: Seeding loads Users (`user@ev.com`, `admin@ev.com`), Stations, Solar Insights, and Charging Ports.

---

## ⚡ 2. Flagship Hub: Nagpur Kalmeshwar
*   **Name**: `"GoBharat EV Flagship Command Hub"`
*   **Address**: `"Kalmeshwar Town Center, Nagpur, Maharashtra 441501"`
*   **Coordinates**: Latitude `21.2333`, Longitude `78.9167`
*   **Rating**: `5.0` (Premium status)
*   **Solar Metrics**: Output: `80.0` kW, Storage: `300.0` kWh, Score: `100% Green` renewable power.
*   **Charging Sockets**:

| Port Type | Power | Price | Operational Status |
| :--- | :--- | :--- | :--- |
| **CCS2 Supercharger** | 350 kW | ₹15.0/kWh | AVAILABLE |
| **CCS2 Charger** | 150 kW | ₹12.0/kWh | AVAILABLE |
| **Type 2 AC Charger** | 22 kW | ₹8.0/kWh | AVAILABLE |

---

## 🗺️ 3. Geographic States & Networks
The seed lists contain **25 stations** spread across **10 key states and territories** of India:

*   **Maharashtra**: Mumbai, Pune, Lonavala, Nagpur.
*   **Delhi NCR**: New Delhi, Gurugram, Noida.
*   **Karnataka**: Bengaluru, Whitefield.
*   **Tamil Nadu**: Chennai, Krishnagiri.
*   **Telangana**: Shamshabad, Gachibowli.
*   **West Bengal**: Kolkata, Howrah.
*   **Gujarat**: Ahmedabad, Surat.
*   **Kerala**: Kakkanad, Kochi, Thiruvananthapuram.
*   **Rajasthan**: Jaipur, Udaipur.
