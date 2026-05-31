# Product Requirements Document (PRD) - GoBharat EV

---

## 1. Executive Summary & Product Vision
**GoBharat EV** is India’s first topography-aware electric vehicle routing network and solar charging station coordinator. 

Standard map applications calculate EV routing purely based on flat, point-to-point Euclidean distances. This critical limitation leads to unexpected roadside depletions in high-altitude climbs (such as the Lonavala/Khandala climbs in the Western Ghats). 

GoBharat EV bridges the gap between core physical sciences and software systems by evaluating gravity force vectors, monsoonal tire-asphalt wet drag, kinetic regenerative recapture, and cabin A/C thermal auxiliary loads. In addition, it ranks public charging ports by live solar renewability scores, encouraging drivers to charge their vehicles with clean electrons.

---

## 2. Core Target Audience
*   **Electric Vehicle Owners**: Drivers requiring high-fidelity range estimations on mountainous and national expressways.
*   **Fleet Managers**: Commercial operators who need real-time station diagnostics and override grids to maintain optimal uptime.
*   **Eco-Conscious Commuters**: Drivers looking to minimize carbon footprints by matching charging sessions with high solar renewability yields.

---

## 3. High-Level Feature List

### 🗺️ Feature 1: Topography-Aware Route Coordinator
*   **Scope**: Solve optimal paths between junctions using elevation-profile datasets.
*   **Requirements**:
    *   Dynamic slider to input vehicle starting State-of-Charge (SoC).
    *   Dropdown to select pre-configured EV models (e.g. Tata Nexon EV, Ather 450X, Tesla Model Y/3, BYD Atto 3, Nissan Leaf, Audi e-tron, Porsche Taycan, MG ZS EV).
    *   Interactive map coordinate plots demonstrating route trajectory.

### 🔌 Feature 2: Charging Station Locator
*   **Scope**: Render charging terminals globally across multiple nations with real-time port statuses.
*   **Requirements**:
    *   Custom icons reflecting charger availability (Green: Available, Orange: Occupied, Pink: Maintenance).
    *   Popup details showing port connector types, power output (kW), pricing, and solar energy indices.

### 📡 Feature 3: Dynamic Map Filters (Global Navigation)
*   **Scope**: Dynamic cascading dropdowns filtering the map by Country, State, and City.
*   **Requirements**:
    *   Auto-scaling selectors extracting unique countries, states, and cities dynamically from active seed address fields.
    *   Smooth Leaflet viewport centering: zooming directly (`setView` level `12`) for single targets (like Nagpur), and fitting boundaries (`fitBounds`) for multi-pin results.

### 🔋 Feature 4: Live OCPP Sandbox & Charging Curves
*   **Scope**: Interactive charging simulation showing power flow scaling.
*   **Requirements**:
    *   Line chart canvas drawing dynamic charging curves (constant-current vs. constant-voltage tapering after 80% SoC).
    *   Interactive diagnostic controllers to inject status faults (`OVER_VOLTAGE`, `THERMAL_LOCK`) and trigger instantaneous WebSocket operator alerts.

### 🏢 Feature 5: Operations & Support Ticket Console
*   **Scope**: End-to-end persistent driver inquiry ticketing pipeline.
*   **Requirements**:
    *   Driver submission form yielding unique persistent UUIDs.
    *   Operations ticket dashboard inside `/admin` letting operators review, mark as resolved, or permanently delete queries.

---

## 4. Success Metrics
*   **Range Prediction Precision**: Maintain range predictions within 99% accuracy relative to simulated physical environments.
*   **Telemetry Latency**: WebSocket status updates broadcasted and painted on map portals in under 500 milliseconds.
*   **UX Accessibility**: Fully responsive sidebar navigation maintaining fluid layouts across both desktop and mobile screens.
