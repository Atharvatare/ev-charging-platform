# Walkthrough: Nagpur Localization & Map Filters

## 🏗️ 1. Technical Implementation Details

### Flagship Station Seeding
- Created `"GoBharat EV Flagship Command Hub"` centered at Kalmeshwar Town Center, Nagpur, Maharashtra (441501) with coordinates Latitude `21.2333`, Longitude `78.9167` inside `app/core/seed.py`.
- Configured 3 high-power ports (350kW CCS2, 150kW CCS2, 22kW Type 2 AC) with ₹15/kWh, ₹12/kWh, and ₹8/kWh rates.
- Loaded 80kW Solar Output and 300kWh Battery Storage, achieving a `100% Green` renewable score.
- Raised database re-seeding threshold to 25 stations.

### Corporate Office Relocation
- Updated `/support` template registered office to: **Startup Command Hub, Kalmeshwar, Nagpur, Maharashtra 441501**.

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
