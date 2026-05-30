# Specification: Topographic A* Routing & Physical Science Solver

This specification documents the physical science equations, A* graph networks, and weather coefficients used to calculate EV range depletion on the **GoBharat EV** platform.

---

## ⚡ 1. Physics Consumption Equations
The physics core located in [`app/engines/battery.py`](file:///d:/EV%20CHARGING/app/engines/battery.py) computes energy consumption based on force vectors acting on the vehicle:

$$F_{total} = F_{gravity} + F_{rolling} + F_{aerodynamic}$$

1.  **Gravity Force ($F_{gravity}$)**:
    $$F_{gravity} = m \cdot g \cdot \sin(\theta)$$
    *   Where $m$ is vehicle mass (kg) and $\theta$ is elevation gradient.
2.  **Rolling Resistance Force ($F_{rolling}$)**:
    $$F_{rolling} = m \cdot g \cdot C_{rr} \cdot \cos(\theta)$$
    *   Where $C_{rr}$ is the rolling resistance coefficient (wet drag increases this by 15% during monsoons).
3.  **Aerodynamic Drag Force ($F_{aerodynamic}$)**:
    $$F_{aerodynamic} = \frac{1}{2} \cdot \rho \cdot C_d \cdot A \cdot v_{rel}^2$$
    *   Where $C_d$ is drag coefficient, $A$ is frontal area ($m^2$), and $v_{rel}$ is air speed adjusting for headwinds/tailwinds.

### Kinetic Energy Recapture (Regen)
When driving downhill ($\theta < 0$), gravity assists the vehicle. Kinetic energy is fed back through the regenerative braking algorithm back to the battery, reflecting positive State of Charge (SoC) offsets:

$$E_{regen} = F_{total} \cdot d \cdot \eta_{regen}$$

---

## 🗺️ 2. Topographic A* Graph Network
The routing router in [`app/engines/router.py`](file:///d:/EV%20CHARGING/app/engines/router.py) maps a directed topographic network connecting major junctions and hubs:

*   **Gateway of India** (lat: `18.9220`, lng: `72.8347`, elev: `2m`)
*   **Lower Parel** (lat: `18.9950`, lng: `72.8250`, elev: `6m`)
*   **BKC Hub** (lat: `19.0600`, lng: `72.8600`, elev: `4m`)
*   **Chembur Junction** (lat: `19.0620`, lng: `72.8980`, elev: `8m`)
*   **Vashi Bridge** (lat: `19.0430`, lng: `72.9850`, elev: `12m`)
*   **Lonavala Expressway Stop** (lat: `18.7500`, lng: `73.4000`, elev: `620m`)
*   **Khandala Hairpin** (lat: `18.7610`, lng: `73.3750`, elev: `550m`)
*   **Pune Aundh** (lat: `18.5584`, lng: `73.8078`, elev: `560m`)

---

## ⛈️ 3. Weather & Climate Coefficients

| Factor | Operational Impact | Technical Scaling |
| :--- | :--- | :--- |
| **Headwind** | Increases relative velocity $v_{rel} = v + v_{wind}$ | Rises absolute aerodynamic force drag quadratically. |
| **Tailwind** | Decreases relative velocity $v_{rel} = v - v_{wind}$ | Decreases aerodynamic drag. |
| **Monsoon Rain** | Increases $C_{rr}$ by 15% due to water friction | Raises rolling resistance consumption by 15%. |
| **Extreme Heat** | High PTC A/C auxiliary load $P_{aux} = 3500\text{W}$ | Constant drain on battery regardless of speed. |
