"""
fare_calculator.py
Urban Black REAL fare calculator — updated with fixed economy/premium data.

Rules applied:
- Base fare: Rs 55 for 1.5 km
- Incremental charge based on total km:
    < 15 km: Rs 25 / km
    15 to <18 km: Rs 23 / km
    18 to <20 km: Rs 22 / km
    20+ km: Rs 20 / km
- Waiting charges: First 5 minutes free, then Rs 2 per minute
- Night charges: 25% extra (multiplier 1.25)
- Weather surge: 10-20% depending on conditions (multiplier 1.10 - 1.20)
- GST: 5%
"""
import math
import random

def compute_fare(
    km: float,
    is_ac: bool,
    trip_type: str,
    hour: int,
    wait_time_min: float = 0.0,
    weather_surge: float = 1.0,  # default 1.0 meaning no surge
    is_holiday: bool = False,
    noise_pct: float = 0.0,
) -> dict:
    """
    Compute fare using the real Urban Black rate structure.
    """
    # 1. Base fare and distance logic
    base_fare_fixed = 55.0  # For first 1.5km
    incremental_km = max(0.0, float(km) - 1.5)
    
    # Determine the per-km rate for incremental distance
    if km < 15:
        rate_per_km = 25.0
    elif 15 <= km < 18:
        rate_per_km = 23.0
    elif 18 <= km < 20:
        rate_per_km = 22.0
    else:  # 20+
        rate_per_km = 20.0
        
    distance_fare = base_fare_fixed + (incremental_km * rate_per_km)
    
    # Apply AC modifier (assuming standard 10% bump for premium if desired)
    if is_ac:
        distance_fare *= 1.10
        
    # 2. Waiting charges (First 5 min free, then Rs 2/min)
    billable_wait = max(0.0, wait_time_min - 5.0)
    wait_charge = billable_wait * 2.0
    
    # 3. Night charge (+25% during 22:00 to 06:00)
    is_night = hour >= 22 or hour < 6
    night_adj = (distance_fare * 0.25) if is_night else 0.0
    
    # 4. Weather surge (+10% to 20%)
    # weather_surge parameter should be e.g. 1.15 for 15% surge
    weather_adj = distance_fare * max(0.0, weather_surge - 1.0)
    
    # 5. Holiday (keeping an 8% holiday bump for completeness if provided)
    holiday_adj = distance_fare * 0.08 if is_holiday else 0.0
    
    subtotal = distance_fare + wait_charge + night_adj + weather_adj + holiday_adj
    
    # Noise parameter
    if noise_pct > 0:
        subtotal *= 1 + random.uniform(-noise_pct, noise_pct)
        
    # 6. GST (5%) applied to the absolute final subtotal
    gst = subtotal * 0.05
    final_offered = round(subtotal + gst, 2)
    
    return {
        "offered_fare": final_offered,
        "base_fare_fixed": round(base_fare_fixed, 2),
        "distance_fare": round(distance_fare, 2),
        "wait_charge": round(wait_charge, 2),
        "night_adj": round(night_adj, 2),
        "weather_adj": round(weather_adj, 2),
        "holiday_adj": round(holiday_adj, 2),
        "gst_5_percent": round(gst, 2),
        "incremental_km": round(incremental_km, 2),
        "rate_per_km_used": rate_per_km,
        "per_km": round(final_offered / km, 2) if km > 0 else 0
    }

def predict_fare(sample: dict) -> dict:
    """
    Wrapper for compute_fare accepting a sample dict.
    """
    km = sample.get("estimated_distance_km", sample.get("actual_distance_km", 0.0))
    is_ac = str(sample.get("vehicle_type", "economy")).lower() == "premium"
    trip_type = sample.get("trip_type", "standard")
    
    # Approximate hour based on peak flag if hour is not explicitly provided
    if "hour_of_day" in sample:
        hour = int(sample["hour_of_day"])
    else:
        is_peak = sample.get("is_peak_hour", False)
        # Default to 18 (e.g. 6 PM evening peak) or 12 noon
        hour = 18 if is_peak else 12
        
    # Extract waiting time and weather surge
    wait_time = float(sample.get("wait_time_min", 0.0))
    weather_surge = float(sample.get("weather_surge", 1.0))
            
    return compute_fare(
        km=km, 
        is_ac=is_ac, 
        trip_type=trip_type, 
        hour=hour,
        wait_time_min=wait_time,
        weather_surge=weather_surge
    )

if __name__ == "__main__":
    print("Testing Updated Real Fare Logic:")
    samples = [
        (10, False, 12, 0, 1.0),   # 10km short/med, non-AC, noon, no wait, no surge
        (16, False, 12, 0, 1.0),   # 16km long, non-AC, noon
        (19, True,  23, 10, 1.15), # 19km, AC, 11PM (night), 10m wait, 15% weather surge
        (25, False, 8,  0, 1.0),   # 25km long, non-AC, 8AM
    ]
    
    for km, ac, h, wait, surge in samples:
        r = compute_fare(km, ac, "standard", h, wait, surge)
        print(
            f"  {km:>4}km | AC:{str(ac):<5} | Hr:{h:>2} | Wait:{wait:>2}m | Surge:{surge:.2f} "
            f"-> Total: \u20b9{r['offered_fare']:.2f}  (Rate: \u20b9{r['rate_per_km_used']}/km)"
        )
