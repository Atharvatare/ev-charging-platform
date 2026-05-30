import sys
sys.path.append('.')
from app.engines.router import compute_route

res = compute_route(origin="Rincon_Center", destination="Twin_Peaks", start_soc=11.0)
print("REROUTED STATUS:", res.get("rerouted"))
print("CHARGER STOP INJECTED:", res.get("charging_station_stop"))
print("PATH NODES:", res.get("nodes"))
print("FINAL SOC:", res.get("final_soc"))

print("\nTELEMETRY DETAIL LOGS:")
for pt in res.get("telemetry", []):
    print(f"Node: {pt['node']:25} | SoC: {pt['soc']}% | Charging Stop: {pt.get('charging_stop')}")
