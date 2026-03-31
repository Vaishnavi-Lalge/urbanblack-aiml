"""
generate_dataset.py
Generate a 50 K synthetic rides dataset that matches the Urban Black
fare rules, shift constraints, and real-data trip-type distribution.

Shift constraints baked in:
  - Shift max duration : 12 hours
  - Min rides/shift    : 25
  - Min distance/shift : 135 km

Trip types (matching real data distribution):
  standard_long (50%), outskirts (25%), airport (15%), intercity (5%), standard (5%)
"""
import csv, uuid, random
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.fare_calculator import compute_fare

NUM_ROWS    = 50_000
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "synthetic_rides_dataset_50k.csv"

VEHICLE_TYPES = ["economy", "premium"]
TRIP_TYPES    = ["standard_long", "outskirts", "airport", "intercity", "standard"]
TRIP_WEIGHTS  = [0.50,            0.25,        0.15,      0.05,        0.05]
FUEL_LEVELS   = ["FULL", "THREE_QUARTER", "HALF", "QUARTER", "LOW"]
CONDITIONS    = ["EXCELLENT", "GOOD", "FAIR", "NEEDS_ATTENTION"]
STATUSES      = ["RIDE_COMPLETED", "CANCELLED"]
DEPOT_ZONES   = ["West-Pune", "Hinjewadi", "East-Pune", "North-Pune", "Airport-Zone", "Central-Pune"]
PEAK_HOURS    = {8, 9, 17, 18, 19, 20}

# Distance ranges per trip type (km)
DIST_RANGES = {
    "standard":      (3.0,  14.9),
    "standard_long": (15.0, 80.0),
    "outskirts":     (15.0, 50.0),
    "airport":       (20.0, 70.0),
    "intercity":     (50.0, 200.0),
}

HEADERS = [
    "trip_id", "request_timestamp", "started_at", "completed_at",
    "hour_of_day", "day_of_week", "is_weekend", "is_peak_hour",
    "pickup_lat", "pickup_lng", "dropoff_lat", "dropoff_lng",
    "approach_km", "actual_distance_km", "estimated_distance_km",
    "actual_duration_min", "estimated_duration_min",
    "vehicle_type", "trip_type",
    "offered_fare", "final_fare",
    "fare_slab_stage_id",
    "driver_id", "driver_rating", "driver_total_trips",
    "driver_shift_hours_elapsed", "driver_online_minutes",
    "driver_fuel_level_start", "driver_vehicle_condition",
    "driver_daily_ride_km", "driver_daily_dead_km",
    "driver_quota_km", "driver_overuse_km",
    "driver_goal_km", "driver_goal_km_reached",
    "depot_zone",
    "rider_acceptance_flag", "first_driver_accepted", "drivers_offered_count",
    "ride_status", "revenue_per_km",
    # shift-level KPI columns
    "driver_shift_rides", "driver_shift_min_reached",
]

def make_driver_pool(n=150):
    pool = []
    for _ in range(n):
        pool.append({
            "id":          str(uuid.uuid4()),
            "rating":      round(random.uniform(3.5, 5.0), 2),
            "total_trips": random.randint(50, 5000),
            "goal_km":     135,
        })
    return pool

def generate_synthetic_dataset(num_rows: int, output_path):
    random.seed(42)
    driver_pool = make_driver_pool()

    # Per-driver shift accumulators  {driver_id: {rides, km}}
    shift_state: dict[str, dict] = {}

    print(f"Generating {num_rows:,} synthetic rides …")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()

        for i in range(num_rows):
            trip_id    = str(uuid.uuid4())
            req_time   = datetime(2025, 1, 1) + timedelta(
                days=random.randint(0, 365),
                minutes=random.randint(0, 24 * 60),
            )
            hour       = req_time.hour
            dow        = req_time.weekday() + 1
            is_weekend = dow >= 6
            is_peak    = hour in PEAK_HOURS

            veh_type   = random.choices(VEHICLE_TYPES, weights=[0.78, 0.22], k=1)[0]
            is_ac      = veh_type == "premium"
            t_type     = random.choices(TRIP_TYPES, weights=TRIP_WEIGHTS, k=1)[0]

            lo, hi     = DIST_RANGES[t_type]
            actual_km  = round(random.uniform(lo, hi), 2)
            est_km     = round(actual_km * random.uniform(0.90, 1.10), 2)
            approach_km= round(random.uniform(0.5, 6.0), 2)
            dur_min    = int(actual_km * random.uniform(1.4, 2.6))
            est_dur    = int(dur_min * random.uniform(0.85, 1.15))

            started_at    = req_time + timedelta(minutes=random.randint(2, 12))
            completed_at  = started_at + timedelta(minutes=dur_min)
            status        = random.choices(STATUSES, weights=[0.85, 0.15], k=1)[0]

            drv           = random.choice(driver_pool)
            drv_id        = drv["id"]

            # ── shift accumulator ──────────────────────────────────────────
            if drv_id not in shift_state:
                shift_state[drv_id] = {"rides": 0, "km": 0.0}
            if status == "RIDE_COMPLETED":
                shift_state[drv_id]["rides"] += 1
                shift_state[drv_id]["km"]    += actual_km

            shift_rides = shift_state[drv_id]["rides"]
            shift_km    = shift_state[drv_id]["km"]
            # Reset when shift completes (12 h worth of rides)
            if shift_rides >= 30:
                shift_state[drv_id] = {"rides": 0, "km": 0.0}

            # ── fare ──────────────────────────────────────────────────────
            wait_min  = max(0.0, (started_at - req_time).total_seconds() / 60.0) \
                        if status == "RIDE_COMPLETED" else 0.0
            surge     = round(random.uniform(1.0, 1.20), 2)
            is_night  = hour >= 22 or hour < 6
            shift_hrs = round(random.uniform(0.5, 12.0), 2)

            fare_r    = compute_fare(
                km=est_km, is_ac=is_ac, trip_type=t_type,
                hour=hour, wait_time_min=wait_min, weather_surge=surge,
            )
            offered   = fare_r["offered_fare"]
            final     = offered if status == "RIDE_COMPLETED" else ""
            rev_per_km= round(offered / actual_km, 2) if status == "RIDE_COMPLETED" and actual_km > 0 else ""

            drv_daily_ride_km = round(random.uniform(10.0, 160.0), 2)

            # Lat/lon (Pune region)
            plat = 18.5204 + random.uniform(-0.15, 0.15)
            plng = 73.8567 + random.uniform(-0.15, 0.15)

            writer.writerow({
                "trip_id":                    trip_id,
                "request_timestamp":          req_time.strftime("%Y-%m-%d %H:%M:%S"),
                "started_at":                 started_at.strftime("%Y-%m-%d %H:%M:%S") if status == "RIDE_COMPLETED" else "",
                "completed_at":               completed_at.strftime("%Y-%m-%d %H:%M:%S") if status == "RIDE_COMPLETED" else "",
                "hour_of_day":                hour,
                "day_of_week":                dow,
                "is_weekend":                 is_weekend,
                "is_peak_hour":               is_peak,
                "pickup_lat":                 round(plat, 6),
                "pickup_lng":                 round(plng, 6),
                "dropoff_lat":                round(plat + random.uniform(-0.25, 0.25), 6),
                "dropoff_lng":                round(plng + random.uniform(-0.25, 0.25), 6),
                "approach_km":                approach_km,
                "actual_distance_km":         actual_km,
                "estimated_distance_km":      est_km,
                "actual_duration_min":        dur_min,
                "estimated_duration_min":     est_dur,
                "vehicle_type":               veh_type,
                "trip_type":                  t_type,
                "offered_fare":               offered,
                "final_fare":                 final,
                "fare_slab_stage_id":         1 if actual_km < 15 else (2 if actual_km < 18 else (3 if actual_km < 20 else 4)),
                "driver_id":                  drv_id,
                "driver_rating":              drv["rating"],
                "driver_total_trips":         drv["total_trips"],
                "driver_shift_hours_elapsed": shift_hrs,
                "driver_online_minutes":      int(shift_hrs * 60),
                "driver_fuel_level_start":    random.choice(FUEL_LEVELS),
                "driver_vehicle_condition":   random.choice(CONDITIONS),
                "driver_daily_ride_km":       drv_daily_ride_km,
                "driver_daily_dead_km":       round(random.uniform(5.0, 45.0), 2),
                "driver_quota_km":            135.0,
                "driver_overuse_km":          round(max(0.0, drv_daily_ride_km - 135.0), 2),
                "driver_goal_km":             drv["goal_km"],
                "driver_goal_km_reached":     round(drv_daily_ride_km / drv["goal_km"] * 100, 2),
                "depot_zone":                 random.choice(DEPOT_ZONES),
                "rider_acceptance_flag":      True if status == "RIDE_COMPLETED" else random.choice([True, False]),
                "first_driver_accepted":      random.choice([True, False]),
                "drivers_offered_count":      random.randint(1, 5),
                "ride_status":                status,
                "revenue_per_km":             rev_per_km,
                "driver_shift_rides":         shift_rides,
                "driver_shift_min_reached":   shift_km >= 135.0,
            })

            if (i + 1) % 10_000 == 0:
                print(f"  … {i + 1:,} rows generated")

    print(f"✅  {num_rows:,} rows → {output_path}")

if __name__ == "__main__":
    generate_synthetic_dataset(NUM_ROWS, OUTPUT_FILE)
