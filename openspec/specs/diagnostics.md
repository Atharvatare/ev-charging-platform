# Specification: Diagnostics, WebSockets, & Charging Curves

This specification documents the real-time OCPP (Open Charge Point Protocol) diagnostic sandboxes, battery charging curve canvas renders, and WebSocket broadcasting protocols.

---

## 🔌 1. Dynamic Charging Curve Scaling
The driver dashboard (`dashboard.html`) renders a live canvas grid tracking charging speeds (kW output) relative to State of Charge (SoC).
*   **Constant Current Phase**: From `15%` to `80%` SoC, power stays locked at maximum connector output (e.g. 150 kW).
*   **Constant Voltage (Tapering) Phase**: Once SoC exceeds `80%`, chemical resistance increases. Power output tapers down exponentially to protect battery chemistry:
    $$P_{scaled} = P_{max} \cdot \left(1 - \frac{\text{SoC} - 80}{20}\right)^{1.5}$$

---

## ⚠️ 2. Fault Injection & Repair Pipeline
Diagnostic sandbox buttons let users inject standard electric vehicle charger faults:
1.  **Fault Types**: `OVER_VOLTAGE`, `THERMAL_LOCK`, `CONNECTOR_FAULT`.
2.  **API Handler**: `POST /api/bookings/port/{id}/fault` triggers state changes.
3.  **State Mapping**: Database status changes from `AVAILABLE` to `MAINTENANCE`.
4.  **WebSocket Stream**: Triggers telemetry broadcasts, painting map pins pink in under 500 milliseconds across all open client browsers.
5.  **Recovery**: Clicking "Clear Fault & Repair" calls `POST /api/bookings/port/{id}/clear-fault`, restoring availability.

---

## 📡 3. WebSocket Telemetry Schema
The WebSocket connection routes via `/ws` managed by `app/ws/connection_manager.py`:

```json
{
  "type": "TELEMETRY_LOG",
  "message": "Broadcast telemetry event logged: OCPP_PORT_STATUS_FAULT",
  "port_id": "UUID-string",
  "status": "MAINTENANCE"
}
```
All connected handshakes receive status packets, keeping operator grids fully persistent and context-aware.
