# Specification: Cyberpunk UI & Sidebar Filters

This specification defines the visual standards, responsive CSS layout fallbacks, and interactive sidebar filters for the **GoBharat EV** map portal.

---

## 💎 1. Visual Aesthetics
GoBharat EV uses a state-of-the-art **glassmorphic cyberpunk theme** driven by dynamic colors and dark-mode tokens:

*   **Primary Background**: Sleek dark space color (`#0a0a0c`).
*   **Card Framework**: Glassmorphic panels with dark transparent backgrounds (`rgba(18, 18, 22, 0.65)`) and micro-glowing borders tailored to status.
*   **Cyber Colors**:
    *   Neon Green (`#22c55e` / `rgb(34, 197, 94)`): Represents available chargers, eco-savings, and successful routes.
    *   Neon Cyan (`#06b6d4`): Represents active SoC graphs and highway hotlines.
    *   Neon Orange (`#f97316`): Represents occupied chargers and climate systems.
    *   Neon Pink (`#ec4899`): Represents ports under maintenance or system faults.

---

## 🗺️ 2. Dynamic Country, State, & City Map Filters
Interactive dropdowns are mounted in the Left HUD Sidebar of `portal.html`, giving drivers immediate map portal control:

### UI Selectors
1.  **Country Dropdown**: Toggle between `All Countries` and `India`.
2.  **State Dropdown**: Reactive state choices dynamically extracted from the database address fields.
3.  **City Dropdown**: Choices scoped exactly to the selected state (e.g. choosing Maharashtra displays Mumbai, Pune, Lonavala, and Nagpur).

### Alpine.js Event Mappings
*   `onCountryChange()`: Resets state and city, filters visible Leaflet markers, and updates map bounds.
*   `onStateChange()`: Resets city, reconstructs visible cities within the chosen state, filters Leaflet markers, and executes camera adjustments.
*   `onCityChange()`: Scopes Leaflet markers strictly to the city and centers the map view directly.

### Address Extraction Regex
```javascript
parseStationAddress(address) {
    const parts = address.split(',').map(p => p.trim());
    if (parts.length < 2) return { city: 'Unknown', state: 'Unknown', country: 'India' };
    
    const lastPart = parts[parts.length - 1];
    // Remove digits (zip codes) to get clean state
    const state = lastPart.replace(/\d+/g, '').trim();
    const city = parts[parts.length - 2];
    
    return { city: city, state: state, country: 'India' };
}
```

---

## 🔌 3. Map Viewport Transitions
Map transitions must feel alive and high-fidelity:
*   **Fit Bounds (`map.fitBounds`)**: Used when multiple stations are selected, centering and zooming the camera to perfectly enfold all filtered pins with a `50px` padding.
*   **Focused Zoom (`map.setView(coords, 12)`)**: Used when a single station remains (such as filtering for Nagpur), zooming in high-fidelity directly to the flagship command hub.
