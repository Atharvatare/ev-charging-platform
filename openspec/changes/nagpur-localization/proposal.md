# Change Proposal: Nagpur Localization & Map Filters

## 1. Goal Description
The purpose of this change is to update **GoBharat EV**'s corporate identity and operational base to center around the solo builder's base in **Kalmeshwar, Nagpur, Maharashtra (441501)**, seed a flagship command hub in Nagpur, and provide interactive state/city map filters.

---

## 2. Technical Decisions
*   **Nagpur Station**: Insert a 25th flagship charging hub with high-power AC/DC sockets, solar telemetry output, and full green renewability metrics in `app/core/seed.py`.
*   **Headquarters Address**: Replace Bandra Kurla Complex (BKC), Mumbai references with **Startup Command Hub, Kalmeshwar, Nagpur, Maharashtra 441501** in the support templates.
*   **Sidebar Dropdowns**: Embed glassmorphic filters for Country, State, and City directly inside the Left HUD Route Coordinator panel, using regex parser logic to dynamically extract values from database seeds.
*   **Leaflet Camera Fitting**: Connect visible markers to `map.fitBounds` (for states) and detailed focused zoom (level `12` for single cities) to ensure high-fidelity viewport panning.
