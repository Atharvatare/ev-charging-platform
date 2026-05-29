import random
from typing import Dict, Any

def forecast_station_queue(
    total_ports: int,
    occupied_ports: int,
    hour_of_day: int
) -> Dict[str, Any]:
    """
    Predicts charger queue lengths and driver wait times based on live occupancy metrics, 
    charger capacity levels, and time-of-day demand coefficients.
    """
    if occupied_ports < total_ports:
        # Ports are available, no wait time!
        return {
            "predicted_wait_minutes": 0,
            "queue_length": 0,
            "utilization_rate": round((occupied_ports / max(total_ports, 1)) * 100, 1),
            "demand_status": "LOW" if hour_of_day not in [8, 9, 17, 18] else "MEDIUM"
        }

    # Rush hour demand factors (e.g. peak morning 8-10 AM and evening 5-7 PM commute)
    is_peak = hour_of_day in [8, 9, 17, 18, 19]
    is_mid_day = hour_of_day in [11, 12, 13, 14, 15, 16]

    # Calculate utilization rate (all ports full, so 100% or higher simulated load)
    base_wait = 15.0 if not is_peak else 25.0
    if is_mid_day:
        base_wait = 18.0

    # Add minor random noise to simulate natural driver deviations
    random.seed(total_ports + occupied_ports + hour_of_day)
    simulated_wait = base_wait + random.uniform(-3.0, 5.0)

    # Queue length estimation (simulated based on ports capacity)
    simulated_queue = int(total_ports * (1.5 if is_peak else 0.8))
    simulated_queue = max(simulated_queue, 1)

    # Adjusted average wait time is divided across all parallel operational ports
    actual_wait_estimate = (simulated_wait * simulated_queue) / max(total_ports, 1)
    actual_wait_estimate = round(max(actual_wait_estimate, 5.0), 1)

    demand_level = "CRITICAL" if is_peak else ("HIGH" if is_mid_day else "NORMAL")

    return {
        "predicted_wait_minutes": actual_wait_estimate,
        "queue_length": simulated_queue,
        "utilization_rate": 100.0,
        "demand_status": demand_level
    }
