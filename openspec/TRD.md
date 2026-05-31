# Technical Requirements Document (TRD) - GoBharat EV

---

## 1. Core Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.14+ | Standard microservices backend environment. |
| **Framework** | FastAPI | High-speed, asynchronous ASGI web framework. |
| **ORM Mock** | SQLModel (Custom Emulator) | Emulates database model declarations with auto-types namespace rebuilds. |
| **Database** | MockDBStore (In-Memory) | High-speed, thread-safe dict store representing persistent SQLAlchemy tables. |
| **Mapping Library**| Leaflet.js (v1.9.4) | Interactive vector map engine rendering CartoDB dark tile layers. |
| **Client Core** | Alpine.js (v3.13) | Lightweight reactive front-end micro-framework driving dashboard variables. |
| **UI Styles** | Tailwind CSS / DaisyUI | Cyberpunk design framework with dynamic light/dark CSS custom variables. |
| **Streaming Feed** | WebSocket Protocol | Continuous full-duplex JSON broadcast streaming port updates. |

---

## 2. Dynamic APIs & Routing Endpoint Specification

### 🔑 Authentication (Microservice Auth Router)
*   `POST /api/auth/register`: Register new drivers (returns name, phone, email, and wallet starting balance of ₹100.0).
*   `POST /api/auth/login`: Form-encoded credentials verification returning bearer access tokens.

### 🗺️ Physical Route Solver
*   `POST /api/routing/plan`: Evaluates A* path calculations across topographic nodes, incorporating environmental drag parameters.
*   `POST /api/routing/compare`: Simulates route calculations in parallel across all standard EV models.

### 🔋 Charging Station Inventory
*   `GET /api/stations/`: Retrieves all seeded stations, including active ports and real-time solar insight matrices.
*   `PATCH /api/stations/{st_id}/ports/{port_id}/status`: Dynamic operator status override endpoint.

### 📡 Real-Time OCPP Telemetry
*   `WS /ws`: Asynchronous WebSocket pipeline broadcasting state statuses and diagnostic heartbeats.

### 🏢 Operations Support Tickets
*   `POST /api/contact/submit`: Log ticket persistently into database schemas (returns generated UUID).
*   `GET /api/contact/tickets`: Fetch all driver support tickets (sorted desc).
*   `PATCH /api/contact/tickets/{id}/status`: Set status to `RESOLVED` or `OPEN`.
*   `DELETE /api/contact/tickets/{id}`: Discard support ticket.

---

## 3. Physical Science Solver Formulas
The physics engine located in [`app/engines/battery.py`](file:///d:/EV%20CHARGING/app/engines/battery.py) evaluates force vectors acting on the vehicle:

$$F_{total} = F_{gravity} + F_{rolling} + F_{aerodynamic}$$

1.  **Gravity Force ($F_{gravity}$)**:
    $$F_{gravity} = m \cdot g \cdot \sin(\theta)$$
2.  **Rolling Resistance Force ($F_{rolling}$)**:
    $$F_{rolling} = m \cdot g \cdot C_{rr} \cdot \cos(\theta)$$
    *   *Monsoon Rain*: Scaling $C_{rr}$ by `1.15` (15% wet drag friction scale).
3.  **Aerodynamic Drag Force ($F_{aerodynamic}$)**:
    $$F_{aerodynamic} = \frac{1}{2} \cdot \rho \cdot C_d \cdot A \cdot (v - v_{wind})^2$$
    *   *Headwind*: Velocity relative is $v + v_{wind}$.
    *   *Tailwind*: Velocity relative is $v - v_{wind}$.

---

## 4. WebSocket Broadcast Telemetry Schema
WebSocket events are serialized and pushed to connected browser viewports in standard JSON format:

```json
{
  "type": "PORT_STATUS_UPDATE",
  "station_id": "UUID-string",
  "port_id": "UUID-string",
  "status": "MAINTENANCE"
}
```
Client portals intercepting this payload dynamically alter local markers on the Leaflet layer without requiring page refreshes.
