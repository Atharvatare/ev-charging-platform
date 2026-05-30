# Walkthrough: Nagpur Localization & Map Filters

## 🏗️ 1. Technical Implementation Details

### Flagship Station Seeding
- Created `"GoBharat EV Flagship Command Hub"` centered at Kalmeshwar Town Center, Nagpur, Maharashtra (441501) with coordinates Latitude `21.2333`, Longitude `78.9167` inside `app/core/seed.py`.
- Configured 3 high-power ports (350kW CCS2, 150kW CCS2, 22kW Type 2 AC) with ₹15/kWh, ₹12/kWh, and ₹8/kWh rates.
- Loaded 80kW Solar Output and 300kWh Battery Storage, achieving a `100% Green` renewable score.
- Raised database re-seeding threshold to 25 stations.

### Corporate Office Relocation
- Updated `/support` template registered office to: **Startup Command Hub, Kalmeshwar, Nagpur, Maharashtra 441501**.

### Persistent Support Ticketing System
- **Database Entity Model**: Created `SupportTicket` model in `app/models/ticket.py` with name, email, subject, message, status ("OPEN", "RESOLVED"), and timestamp fields.
- **Mock DB Integration**: Registered model inside `sqlmodel.py` and `database.py`, and added a mock `InMemorySession.delete()` implementation to complete the REST CRUD flow.
- **REST Endpoints**: Integrated dynamic API routes in `app/main.py`: `POST /api/contact/submit` (generates persistent UUID), `GET /api/contact/tickets` (lists all tickets desc), `PATCH /api/contact/tickets/{id}/status` (marks resolved/reopens), and `DELETE /api/contact/tickets/{id}` (discards ticket).
- **Operations Support Queue**: Embedded a beautiful glassmorphic Operations Ticket Queue in the Fleet Admin dashboard (`admin.html`) listing all driver queries in real-time with resolve/reopen and delete actions, fully binding the dashboard to backend database states.

### Interactive Sidebar Filters
- Implemented three beautiful glassmorphic dropdowns (Country, State, City) in the Left HUD Route Coordinator panel.
- Coded robust `parseStationAddress()` regex in Alpine.js component to extract clean State and City fields dynamically.
- Programmed Leaflet view fitting:
  - Selecting a state filters markers and executes `map.fitBounds` with a `50px` padding.
  - Selecting a single city/station (like Nagpur) executes `map.setView(coords, 12)`, centering and zooming directly into the flagship command hub.

---

## 🧪 2. Verification Records
Passed pytest suite verifying routing, battery decay vectors, auth, OCPP diagnostics, and SQLite station count updates:

```bash
cmd /c "set PYTHONPATH=. && venv\Scripts\pytest tests/"
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\EV CHARGING
plugins: anyio-4.13.0
collected 10 items

tests\test_main.py ..........                                            [100%]

====================== 10 passed, 117 warnings in 2.75s =======================
```
