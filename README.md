# GoBharat EV: AI-Powered Topography Route Coordinator & Smart Charger Locator

GoBharat EV is a production-grade, full-stack electric vehicle (EV) coordinate routing network and solar charging station coordinator. Standard map systems calculate EV routing purely based on flat, point-to-point Euclidean distances. This critical limitation leads to unexpected roadside depletions in high-altitude climbs (such as the Lonavala climbs in the Western Ghats). 

GoBharat EV bridges the gap between core physical sciences and software systems by evaluating gravity force vectors, monsoonal tire-asphalt wet drag, tailwind/headwind forces, kinetic regenerative braking, and cabin HVAC auxiliary thermal loads. In addition, it ranks public charging ports by live solar renewability scores, encouraging drivers to charge their vehicles with clean, green electrons.

---

## 🏗️ System Architecture

```mermaid
graph TD
    %% Unified App Container
    subgraph FastAPI_App [Unified FastAPI Full-Stack Engine]
        subgraph Views [Jinja2 Template UI]
            UI_Landing[Hero Dashboard]
            UI_Map[CartoDB Dark Map Portal]
            UI_Dashboard[Wallet & Bookings Dashboard]
            UI_Admin[Operator Socket Override Grid]
            UI_Support[Support Hub]
            UI_About[About Hub]
        end

        subgraph Server [FastAPI Backend Service]
            Router[API Routers & Middleware]
            Auth[JWT Security & RBAC]
{{ ... }}
    Client <--> RealTime
    Client <--> Router

    %% Caching & Storage
    subgraph Storage [Storage & Telemetry Layer]
        SQLite[(Self-Healing SQLite / Supabase PostgreSQL)]
    end

    %% API Connections
    Router <--> SQLite
    Router <--> GoogleMaps[Nominatim / Overpass OSM GIS]
```

---

## ⚡ The EV Charging & Booking Process Flow

```
[Plan Route] ──► [Battery SoC Check] ──► [Low SoC warning? (SoC < 12%)]
                                                       │
         ┌─────────────────────────────────────────────┘
         ▼ (Yes)
[Locate Closest DC Fast Charger via GIS Index]
         │
         ▼
[Insert Charger as Optimal Stop on Graph] ──► [Lock Charger Slot] ──► [Deduct Start Fee]
                                                                                 │
                                                                                 ▼
[Recharge vehicle to 85%] ◄── [Verify QR scanner at post] ◄── [Generate Cryptographic QR]
```

1. **Topography-Aware Pathfinding:** The user plans a trip selecting coordinates. GoBharat EV solves the path using a **custom A* solver** that weighs edge distances alongside elevation slopes.
2. **State of Charge (SoC) Projection:** The physics engine calculates energy drain across each road segment. 
3. **Emergency DC Charger Insertion:** If the vehicle's projected SoC falls below 12% at any node, path calculation is intercepted at the last safe node. The system query filters the database to find the closest reachable fast-charger, inserts it as a waypoint, and plans a multi-stop path.
4. **Port Lockout & Booking:** Drivers select a port at the target station (e.g. 250kW CCS2) and reserve it. This locks the port state to `OCCUPIED` in the database, charges a base reservation fee from their wallet, and compiles a secure cryptographic **QR Access Token**.
5. **Access Scan & OCPP Telemetry:** When arriving at the station, the driver scans the QR code. This triggers an OCPP WebSocket handshake simulation, releasing the socket and initiating charging.

---

## 🧮 Physics & Optimization Mathematics

### 1. Physics-Based Battery State-of-Charge (SoC) Estimator
To accurately predict remaining energy at destination, we evaluate the absolute mechanical forces acting on the vehicle:

$$P_{total} = P_{aerodynamic} + P_{rolling} + P_{gravity} + P_{auxiliary}$$

* **Aerodynamic Drag ($P_{aerodynamic}$):** Evaluates fluid wind resistance, accounting for headwinds/tailwinds:
  $$P_{aerodynamic} = \frac{1}{2} \rho C_d A v_{rel}^2 v$$
  * $\rho$ = Sea-level air density ($1.225 \text{ kg/m}^3$)
  * $C_d$ = Drag coefficient ($0.29$ for Tata Nexon EV)
  * $A$ = Frontal area ($2.4 \text{ m}^2$)
  * $v_{rel}$ = Relative air velocity ($v \pm v_{wind}$)
* **Rolling Resistance ($P_{rolling}$):** Evaluates tire friction (increased by 7% to 15% under wet/monsoonal conditions):
  $$P_{rolling} = C_r m g \cos(\theta) v$$
  * $C_r$ = Rolling resistance coefficient ($0.012$)
  * $m$ = Vehicle mass + payload ($1600 \text{ kg}$)
  * $g$ = Gravitational acceleration ($9.81 \text{ m/s}^2$)
  * $\theta$ = Slope gradient angle ($\text{radians}$)
* **Gravitational Potential ($P_{gravity}$):**
  $$P_{gravity} = m g \sin(\theta) v$$
  * $\theta > 0$ (Climbing): Increases power drain.
  * $\theta < 0$ (Descending): Triggers **regenerative braking** energy capture:
    $$\text{Captured Energy} = \text{Mechanical Force} \times \eta_{regen}$$
    *(recovering up to 70% of potential energy back into the battery capacity)*
* **Auxiliary cabin loads ($P_{auxiliary}$):** Constant HVAC draws scaled dynamically by ambient temperature $+25\%$ under extreme heat ($>32^\circ$C) and $+40\%$ under winter cold ($<10^\circ$C).

### 2. Topography Graph Routing
Traditional routing searches for the shortest path. GoBharat EV weighs each path edge dynamically inside NetworkX using:

$$\text{Weight} = \alpha \cdot \text{Time} + \beta \cdot \text{Energy\_Consumed} + \gamma \cdot \text{Queue\_Delay}$$

---

## 🛠️ Technology Stack

* **Full-Stack Framework:** FastAPI (Asynchronous ASGI server serving APIs, WebSockets, and HTML views).
* **Frontend HUD Canvas:** Jinja2 templates, Tailwind CSS, DaisyUI (cybernetic premium dark-mode panels), and Alpine.js (dynamic reactive client-side bindings).
* **Map Engine:** Leaflet.js styled with the pitch-black **CartoDB Dark Matter** skin.
* **Database & ORM:** SQLModel (SQLAlchemy + Pydantic) connecting to PostgreSQL/SQLite databases.
* **Optimization Systems:** NetworkX (Directed spatial road graphs) & NumPy (mechanical physics matrices).
* **Real-time Comms:** WebSockets for live status updates and dispatches.

---

## 📂 Project Layout

```
d:\EV CHARGING\
├── app/
│   ├── main.py                  # App Entrypoint, Static mounts & WebSockets
│   ├── core/                    # System setup, Security & Seeding
│   │   ├── config.py            # Environment configurations
│   │   ├── database.py          # SQLModel Engine and session factories
│   │   └── seed.py              # Seeds 44 high-fidelity stations & accounts
│   │
│   ├── models/                  # SQLModel schemas
│   │   ├── user.py              # Accounts, roles, wallet balance
│   │   ├── station.py           # Chargers, Ports & Solar Insights
│   │   ├── booking.py           # Reservations & Wallet Transaction ledgers
{{ ... }}
│   ├── templates/               # Visual Glassmorphic Jinja2 HTML Views
│   │   ├── base.html            # Core layout & AI Floating Assistant
│   │   ├── landing.html         # Premium Animated Hero spec grid
│   │   ├── portal.html          # Interactive CartoDB Dark Matter map canvas
│   │   ├── dashboard.html       # Wallet deposits & QR Code access
│   │   ├── admin.html           # Fleet operator override chips
│   │   ├── terms.html           # Terms of Service
│   │   ├── privacy.html         # Privacy Policy
│   │   └── about.html           # Corporate profile
│   │
│   └── ws/                      # WebSocket broadcasts
│       └── connection_manager.py
│
├── tests/                       # Pytest test suite
├── docker-compose.yml           # Postgres database container
├── requirements.txt             # Python packages
└── README.md                    # Platform documentation
```

---

## 🚀 How to Run the Platform Locally

Follow these 3 simple steps to boot the entire ecosystem on your local machine:

### Step 1: Install Python Dependencies
Create a virtual environment (recommended) and install our high-performance mathematical and web packages:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Run the FastAPI Server
Boot our asynchronous full-stack server using Uvicorn. On startup, it will automatically migrate all SQLModel database tables, and seed the spatial grid with 44 realistic global charging stations!
```bash
$env:PYTHONPATH="."
venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```

### Step 3: Explore the Platform
Open your browser and navigate to:
* **Landing Portal:** `http://127.0.0.1:8000/`
* **Interactive Map:** `http://127.0.0.1:8000/portal`
* **Driver Dashboard:** `http://127.0.0.1:8000/dashboard`
* **Admin Health Grid:** `http://127.0.0.1:8000/admin`
* **Auto API Documentation:** `http://127.0.0.1:8000/docs` (Interactive Swagger APIs)

---

## 🔑 Seeded Login Accounts
You can log in to the platform using either of the following seeded user accounts:

| User Type | Email Address | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Standard Driver** | `user@ev.com` | `password123` | Testing routes, checkouts, V2G sessions, wallets, and support ticketing. |
| **System Admin** | `admin@ev.com` | `admin123` | Monitoring fleet telemetry dispatches, port overrides, and ticket approvals. |

---

## 🛠️ Verification & Automated Test Suite

We have written a comprehensive verification test suite validating our physics calculations, NetworkX route optimizations, and wait forecasting.

### Running Automated Tests
Run `pytest` to execute all verification assertions:
```bash
$env:PYTHONPATH="."
.\venv\Scripts\pytest tests/
```

### Test Case Verification Summary
1. **`test_battery_physics_climb`:** Asserts that driving up steep hills (e.g. Lonavala) drains more energy than standard flat roads.
2. **`test_battery_physics_regen`:** Asserts that descending steep hills correctly recovers kinetic and potential energy via regenerative braking, generating negative energy delta gains back to the battery.
3. **`test_router_solver_direct`:** Verifies that the NetworkX A* solver successfully routes the car through intersections, returning coordinates and step-by-step state-of-charge decay.
4. **`test_router_low_battery_reroute`:** Validates our **Emergency Low-Battery Fallback System**! If starting SoC is critically low (e.g. 11%), it intercepts A* execution, calculates reachable stations, inserts an ultra-fast CCS2 stop, charges the car to 85%, and routes the remaining path to destination.
5. **`test_queue_forecaster_rush_hour`:** Asserts that wait-times correctly elevate during peak morning commute times based on commute traffic multipliers.
6. **`test_vehicle_profiles_physics`:** Verifies that different vehicle models (Ather 450X scooter vs Hyundai Ioniq 5 Crossover) exhibit distinct physics-based battery depletion and weight impact behavior.
7. **`test_battery_physics_weather_impact`:** Verifies that headwinds, rainfall (wet asphalt resistance), and temperature extremes (HVAC) correctly increase EV battery depletions under the physics model.
8. **`test_persistent_endpoints`:** Verifies that the FastAPI endpoints for wallet deposits, active bookings, contact ticketing, chatbot queries (including map action parser triggers), and OCPP completions respond correctly.
9. **`test_websocket_broadcasts`:** Verifies that the WebSocket telemetry broadcast channel successfully streams live events.
10. **`test_port_fault_injection`:** Verifies that injecting faults forces the port into MAINTENANCE status, and clearing it restores status to AVAILABLE.
11. **`test_isorange_contour`:** Verifies that the isorange reachability bubble computations are mathematically sound and return correct GeoJSON structures.
12. **`test_v2g_arbitrage_settlement`:** Verifies that finishing a bi-directional V2G charging session successfully completes the reservation and deposits the net credits earned back to the driver's database wallet.
