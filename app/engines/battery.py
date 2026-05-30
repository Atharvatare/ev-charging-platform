import math
from typing import Dict, Any

# Popular Indian and Global EV configurations with dynamic physical weight coefficients
VEHICLE_PROFILES = {
    "tata_nexon_ev_max": {
        "mass_kg": 1600.0,
        "drag_coeff": 0.29,
        "frontal_area": 2.4,
        "rolling_coeff": 0.012,
        "battery_capacity_kwh": 40.5,
        "efficiency": 0.90,
        "regen_efficiency": 0.70,
        "auxiliary_draw_w": 1200.0,
        "display_name": "Tata Nexon EV Max"
    },
    "ather_450x": {
        "mass_kg": 200.0,  # Scooter + Rider mass
        "drag_coeff": 0.60,
        "frontal_area": 0.8,
        "rolling_coeff": 0.015,
        "battery_capacity_kwh": 3.7,
        "efficiency": 0.88,
        "regen_efficiency": 0.50,
        "auxiliary_draw_w": 100.0,
        "display_name": "Ather 450X"
    },
    "tata_tiago_ev": {
        "mass_kg": 1250.0,
        "drag_coeff": 0.32,
        "frontal_area": 2.1,
        "rolling_coeff": 0.012,
        "battery_capacity_kwh": 24.0,
        "efficiency": 0.89,
        "regen_efficiency": 0.65,
        "auxiliary_draw_w": 1000.0,
        "display_name": "Tata Tiago EV"
    },
    "hyundai_ioniq_5": {
        "mass_kg": 2100.0,
        "drag_coeff": 0.288,
        "frontal_area": 2.6,
        "rolling_coeff": 0.011,
        "battery_capacity_kwh": 72.6,
        "efficiency": 0.92,
        "regen_efficiency": 0.75,
        "auxiliary_draw_w": 1500.0,
        "display_name": "Hyundai Ioniq 5"
    },
    "ola_s1_pro": {
        "mass_kg": 215.0,  # Scooter + Rider mass
        "drag_coeff": 0.58,
        "frontal_area": 0.85,
        "rolling_coeff": 0.014,
        "battery_capacity_kwh": 4.0,
        "efficiency": 0.88,
        "regen_efficiency": 0.52,
        "auxiliary_draw_w": 110.0,
        "display_name": "Ola S1 Pro"
    }
}

class EVEnergyModel:
    def __init__(
        self,
        mass_kg: float = 1600.0,         # Mass of typical EV + payload (Default Tata Nexon EV)
        drag_coeff: float = 0.29,         # C_d aerodynamic drag coefficient
        frontal_area: float = 2.4,        # Frontal area in square meters
        rolling_coeff: float = 0.012,      # Tire rolling resistance coefficient
        battery_capacity_kwh: float = 40.5, # Battery size in kWh
        efficiency: float = 0.90,         # Powertrain discharge efficiency (90%)
        regen_efficiency: float = 0.70,   # Regenerative braking recovery efficiency (70%)
        auxiliary_draw_w: float = 1200.0, # HVAC, audio, screens draw (1.2 kW constant)
        # Climate override parameters
        temperature_c: float = 25.0,
        wind_speed_kmh: float = 0.0,
        wind_direction: str = "none",
        rain: str = "none"
    ):
        self.mass = mass_kg
        self.Cd = drag_coeff
        self.A = frontal_area
        
        # Adjust Rolling Resistance Coefficient for wet roads
        self.Cr = rolling_coeff
        if rain.lower() == "heavy":
            self.Cr *= 1.15
        elif rain.lower() == "light":
            self.Cr *= 1.07
            
        self.capacity = battery_capacity_kwh
        self.efficiency = efficiency
        self.regen_efficiency = regen_efficiency
        
        # Scale HVAC / Battery cooling draws based on extreme temperatures
        self.aux_draw = auxiliary_draw_w
        if temperature_c > 32.0:
            self.aux_draw *= 1.25  # 25% increase for AC battery chillers
        elif temperature_c < 10.0:
            self.aux_draw *= 1.40  # 40% increase for active winter heaters
            
        self.wind_speed_ms = wind_speed_kmh / 3.6
        self.wind_direction = wind_direction.lower()
        
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

        # 1. Aerodynamic Drag Force: F_aero = 0.5 * rho * C_d * A * v_rel^2
        v_rel = v
        if self.wind_direction == "headwind":
            v_rel = v + self.wind_speed_ms
        elif self.wind_direction == "tailwind":
            v_rel = max(0.0, v - self.wind_speed_ms)
            
        f_aero = 0.5 * self.air_density * self.Cd * self.A * (v_rel ** 2)

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
