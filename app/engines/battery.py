import math
from typing import Dict, Any

class EVEnergyModel:
    def __init__(
        self,
        mass_kg: float = 2000.0,         # Mass of typical EV + payload (e.g. Tesla Model 3)
        drag_coeff: float = 0.23,         # C_d aerodynamic drag coefficient
        frontal_area: float = 2.22,       # Frontal area in square meters
        rolling_coeff: float = 0.01,      # Tire rolling resistance coefficient
        battery_capacity_kwh: float = 75.0, # Battery size in kWh
        efficiency: float = 0.90,         # Powertrain discharge efficiency (90%)
        regen_efficiency: float = 0.70,   # Regenerative braking recovery efficiency (70%)
        auxiliary_draw_w: float = 1500.0  # HVAC, audio, screens draw (1.5 kW constant)
    ):
        self.mass = mass_kg
        self.Cd = drag_coeff
        self.A = frontal_area
        self.Cr = rolling_coeff
        self.capacity = battery_capacity_kwh
        self.efficiency = efficiency
        self.regen_efficiency = regen_efficiency
        self.aux_draw = auxiliary_draw_w
        self.air_density = 1.225          # kg/m^3 standard sea-level air density
        self.g = 9.81                     # m/s^2 acceleration due to gravity

    def calculate_energy_consumption(
        self,
        distance_km: float,
        speed_kmh: float,
        elevation_delta_m: float
    ) -> Dict[str, Any]:
        """
        Uses standard mechanical forces to compute the exact energy consumed 
        during a trip segment, factoring in speed, drag, slope, and cabin HVAC auxiliary draw.
        """
        if distance_km <= 0 or speed_kmh <= 0:
            return {"energy_kwh": 0.0, "soc_delta": 0.0, "regenerative_kwh": 0.0}

        # Conversions
        distance_m = distance_km * 1000.0
        v = speed_kmh / 3.6  # km/h to m/s
        duration_s = distance_m / v
        duration_h = duration_s / 3600.0
        
        # Calculate slope angle in radians
        # theta = arcsin(height_delta / hypotenuse)
        slope_angle = math.asin(min(max(elevation_delta_m / distance_m, -1.0), 1.0))

        # 1. Aerodynamic Drag Force: F_aero = 0.5 * rho * C_d * A * v^2
        f_aero = 0.5 * self.air_density * self.Cd * self.A * (v ** 2)

        # 2. Rolling Resistance Force: F_roll = C_r * m * g * cos(theta)
        f_roll = self.Cr * self.mass * self.g * math.cos(slope_angle)

        # 3. Gravitational Force: F_gravity = m * g * sin(theta)
        f_gravity = self.mass * self.g * math.sin(slope_angle)

        # Total Tractive Force at wheels: F_total = F_aero + F_roll + F_gravity
        f_total = f_aero + f_roll + f_gravity

        # Tractive Power at wheels (Watts): P = F * v
        p_wheels = f_total * v

        # Auxiliary Cabin Power Draw (Watts)
        p_aux = self.aux_draw

        # Convert mechanical wheel power and electrical auxiliary power to total battery draw (Watts)
        if p_wheels >= 0:
            # Battery is discharging (overcoming resistance and/or climbing)
            p_battery = (p_wheels / self.efficiency) + p_aux
            regen_kwh = 0.0
        else:
            # Decelerating or descending: Regenerative braking captures energy
            # Kinetic/potential energy recaptured with regen efficiency
            p_regen = abs(p_wheels) * self.regen_efficiency
            # Auxiliary draws still consume power from the captured energy
            p_battery = -p_regen + p_aux
            regen_kwh = (abs(p_wheels) * duration_h) / 1000.0

        # Total energy consumed in kWh
        energy_kwh = (p_battery * duration_h) / 1000.0

        # Enforce physical constraints: cannot drain or gain more than battery limits
        soc_delta = (energy_kwh / self.capacity) * 100.0

        return {
            "energy_kwh": round(energy_kwh, 4),
            "soc_delta": round(soc_delta, 2),
            "regenerative_kwh": round(regen_kwh, 4),
            "duration_minutes": round(duration_s / 60.0, 1)
        }

# Default global instance
default_ev_model = EVEnergyModel()
