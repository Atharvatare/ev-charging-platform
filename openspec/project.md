# GoBharat EV - OpenSpec Project Worldview

Welcome to the **GoBharat EV** system specification. This document outlines the project worldview, architecture patterns, core technology stack, and engineering guidelines to maintain long-term alignment across AI agents and human developers.

---

## 🚀 Tech Stack Overview

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Core Backend** | Python / FastAPI | Fully asynchronous, lightweight micro-router API structure. |
| **ORM / Database** | SQLModel / SQLite | Hybrid SQLAlchemy + Pydantic model synchronization for high-fidelity state safety. |
| **Interactive Map** | Leaflet.js | High-fidelity interactive mapping layout loaded over CartoDB Dark Matter tiles. |
| **Reactive Frontend** | Alpine.js | Micro-state manager driving immediate UI updates without virtual-DOM overhead. |
| **Styling** | Tailwind CSS / DaisyUI | Custom cyberpunk neon aesthetics, dynamic dark/light CSS variables. |
| **Real-Time Feed** | WebSockets | Automated OCPP diagnostic state updates streamed live to map pins. |

---

## 🏗️ Architecture Mappings

```mermaid
graph TD
    subgraph Client Panel (Frontend)
        A[portal.html Map] <-->|WS Telemetry| B(ws/connection_manager)
        A <-->|HTTP Requests| C(routers/routing)
        D[dashboard.html] <-->|Reserve/Faults| E(routers/bookings)
    end
    
    subgraph Core Engine (Backend)
        C <-->|A* Physics Solver| F[engines/router]
        F <-->|Consumption Vectors| G[engines/battery]
        E <-->|OCPP Diagnostics| H[SQLModel Database]
    end
```

### Key Folders
*   [`app/core/`](file:///d:/EV%20CHARGING/app/core/): Database setup (`database.py`), config overrides (`config.py`), and spatial database seed routines (`seed.py`).
*   [`app/engines/`](file:///d:/EV%20CHARGING/app/engines/): The physical sciences core. Handles topography A* routing solvers (`router.py`), battery decay climbs/descents physics (`battery.py`), and queue predictions (`queue_predictor.py`).
*   [`app/models/`](file:///d:/EV%20CHARGING/app/models/): SQLite entity schemas.
*   [`app/routers/`](file:///d:/EV%20CHARGING/app/routers/): API router endpoints (bookings, routing, wallet, chatbot, auth).
*   [`app/templates/`](file:///d:/EV%20CHARGING/app/templates/): Frontend views. Contains `portal.html` (Leaflet Map Portal), `dashboard.html` (OCPP charging console), `support.html` (Operations ticketing), and `about.html` (Founder details).

---

## ⚡ Engineering Guidelines

1.  **Topography & Physical Science**: Never treat routing as flat point-to-point distance calculations. Every segment's battery decay must balance wind headwinds, weather wet drag friction, temperature HVAC auxiliary draw, and kinetic regenerative recapture.
2.  **Glassmorphic Cyberpunk Design**: Keep styling rich, glowing, and aligned with cyberpunk variables (neon greens, cyans, glowing stats HUD). Never use generic browser default styles.
3.  **Dynamic Filtering**: Keep map queries scalable. Parse addresses in Javascript using dynamic regex rather than hardcoded states/cities, maintaining zero-configuration compatibility for new station inserts.
