# App Flow & Navigation Architecture - GoBharat EV

This document outlines the user journeys, routing directories, button event mappings, and viewport transitions across the **GoBharat EV** web portal.

---

## 🗺️ 1. Global View Routing Structure

The FastAPI application maps the following frontend Jinja2 routes:

| Route Path | Template Target | Description |
| :--- | :--- | :--- |
| `/` | `landing.html` | Interactive landing hero displaying animated stats and cyber panels. |
| `/portal` | `portal.html` | Core map portal displaying CartoDB vector maps and routing solvers. |
| `/dashboard`| `dashboard.html` | Charging sandbox panel showing wallet and dynamic charging curves. |
| `/admin` | `admin.html` | Fleet dashboard displaying override controls and ticketing queue. |
| `/support` | `support.html` | Operations support form with persistent ticketing controls. |
| `/about` | `about.html` | Company about profile presenting founder bios. |
| `/login` | `login.html` | Driver registration and credentials portal. |

---

## 🔄 2. User Journeys & Event Mappings

### 🧭 Journey A: Finding & Filtering Charging Stations
1.  Driver opens [`/portal`](file:///d:/EV%20CHARGING/app/templates/portal.html).
2.  Leaflet maps initialize automatically centered at the India national node (`20.5937, 78.9629`).
3.  Driver navigates to the **Station Finder** glassmorphic card on the Left HUD.
4.  Driver selects a **Country** from the Country Dropdown (e.g. `USA`):
    *   *Event Mapping*: Trigger `onCountryChange()`.
    *   *Viewport Transition*: The State selector dynamically updates to show only states belonging to that country (e.g. `California`, `New York`, `Texas`). Downstream selections (State, City) are auto-cleared. The Map Portal executes `map.fitBounds` to cover all active stations in that country.
5.  Driver selects a **State** (e.g. `California`):
    *   *Event Mapping*: Trigger `onStateChange()`.
    *   *Viewport Transition*: The City selector dynamically updates to show only cities in California (e.g. `Los Angeles`, `San Francisco`, `Santa Monica`). Downstream selections (City) are auto-cleared. The Map Portal executes `map.fitBounds` to cover all active California stations.
6.  Driver selects a **City** (e.g. `Nagpur` or `Santa Monica`):
    *   *Event Mapping*: Trigger `onCityChange()`.
    *   *Viewport Transition*: Map camera executes `map.setView` to focus directly over the city's filtered stations center with a high-fidelity zoom level of `12`.
7.  Driver clicks any station pin:
    *   *Popup Render*: Leaflet bindings open a custom popup showing the station name, active sockets, pricing structure, and the Green Solar Score.
8.  Driver clicks **Reserve Port**:
    *   *Event Mapping*: Modal popup transitions open, letting the user define reservation duration.

### 🚗 Journey B: Topographic Route Planning
1.  Driver accesses the **Route Coordinator** panel inside [`/portal`](file:///d:/EV%20CHARGING/app/templates/portal.html).
2.  Driver inputs:
    *   *Departure Node*: (e.g., `Gateway of India`)
    *   *Destination Node*: (e.g., `Lonavala Expressway Stop`)
    *   *EV Profile*: (e.g., `Tata Nexon EV Max`)
    *   *Start SoC*: (Adjust range slider from `15%` to `100%`)
    *   *Climate & Drag Overrides*: Open climate card to set custom winds, monsoon rain parameters, or temperatures.
3.  Driver clicks **Solve Optimal Path**:
    *   *Viewport Transition*: Triggers floating loader overlays showing `"Solving Spatial Dijkstra Graph..."`.
    *   *Path Rendering*: Draws glowing coordinates and inserts green and red origin/destination nodes on the Leaflet layer.
    *   *SVG Drawer Transition*: Bottom panel slide-up drawer transition (`x-show="routeResult"`) opens automatically, plotting the double-line SVG chart illustrating mountainous elevation gains alongside exact State of Charge (SoC) depletions.
    *   *Hover Event*: Hovering over SVG chart vectors updates Alpine `hoveredIdx` and pops up exact altitude and battery metrics tooltips.

### 🔌 Journey C: Simulated Charging & OCPP Fault Injection
1.  Driver opens the dashboard ([`/dashboard`](file:///d:/EV%20CHARGING/app/templates/dashboard.html)).
2.  Driver navigates to active bookings, selects an active reservation, and clicks **Start Charge**:
    *   *UI Transition*: Launches diagnostic OCPP Charging modal console.
3.  The HTML5 `<canvas>` launches, dynamically plotting live power inputs scaling up to `150kW`. As the charge reaches `80%`, the curve tapers down.
4.  Driver clicks **Over-voltage Trip** diagnostic fault button:
    *   *API Event*: Posts fault command to backend (`POST /api/bookings/port/{id}/fault`).
    *   *WebSocket Broadcast*: WebSocket sends state update.
    *   *UI Transition*: Charging canvas line turns red, timer freezes, charging power plummets to 0 kW, and the status changes to `MAINTENANCE`. Simultaneously, the portal map pin changes to pink across all operators.
5.  Driver clicks **Clear Fault & Repair**:
    *   *API Event*: Clears fault (`POST /api/bookings/port/{id}/clear-fault`).
    *   *WebSocket Broadcast*: Sends recovery update.
    *   *UI Transition*: Status resets to `AVAILABLE`, and charging restarts cleanly.
