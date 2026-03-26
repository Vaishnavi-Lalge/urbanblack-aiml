import csv
import uuid
from datetime import datetime, timedelta
import random
from pathlib import Path
import sys

# Ensure src module is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.fare_calculator import compute_fare

NUM_ROWS = 50000
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "synthetic_rides_dataset_50k.csv"

def generate_synthetic_dataset(num_rows: int, output_path: str):
    random.seed(42)
    
    cities = ["West-Pune", "Hinjewadi", "East-Pune", "North-Pune", "Airport-Zone", "Central-Pune"]
    vehicle_types = ["economy", "premium"]
    trip_types = ["standard", "outskirts", "airport", "intercity"]
    fuel_levels = ["FULL", "THREE_QUARTER", "HALF", "QUARTER", "LOW"]
    conditions = ["EXCELLENT", "GOOD", "FAIR", "NEEDS_ATTENTION"]
    statuses = ["RIDE_COMPLETED", "CANCELLED"]

    # Pre-generate some random drivers
    driver_pool = []
    for _ in range(100):
        driver_pool.append({
            "id": str(uuid.uuid4()),
            "rating": round(random.uniform(3.5, 5.0), 2),
            "total_trips": random.randint(50, 3000),
            "goal_km": 135
        })

    print(f"Generating {num_rows} synthetic rides...")
    
    headers = [
        "trip_id", "request_timestamp", "started_at", "completed_at", "hour_of_day",
        "day_of_week", "is_weekend", "is_peak_hour", "pickup_lat", "pickup_lng", 
        "dropoff_lat", "dropoff_lng", "approach_km", "actual_distance_km",
        "estimated_distance_km", "actual_duration_min", "estimated_duration_min",
        "vehicle_type", "trip_type", "offered_fare", "final_fare", "fare_slab_stage_id",
        "driver_id", "driver_rating", "driver_total_trips", "driver_shift_hours_elapsed",
        "driver_online_minutes", "driver_fuel_level_start", "driver_vehicle_condition",
        "driver_daily_ride_km", "driver_daily_dead_km", "driver_quota_km",
        "driver_overuse_km", "driver_goal_km", "driver_goal_km_reached", "depot_zone",
        "rider_acceptance_flag", "first_driver_accepted", "drivers_offered_count",
        "ride_status", "revenue_per_km"
    ]
    
    # We'll stream directly to CSV to save memory (even though 50k dicts is fine)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for i in range(num_rows):
            trip_id = str(uuid.uuid4())
            
            # Time constraints
            request_time = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 365), minutes=random.randint(0, 24*60))
            hour_of_day = request_time.hour
            day_of_week = request_time.weekday() + 1
            is_weekend = day_of_week >= 6
            is_peak_hour = hour_of_day in [8, 9, 17, 18, 19, 20]
            
            # Ride logistics
            veh_type = random.choices(vehicle_types, weights=[0.8, 0.2], k=1)[0]
            is_ac = True if veh_type == "premium" else False
            t_type = random.choices(trip_types, weights=[0.5, 0.2, 0.2, 0.1], k=1)[0]
            
            # Distances
            actual_distance_km = round(random.uniform(5.0, 80.0), 2)
            estimated_distance_km = round(actual_distance_km * random.uniform(0.9, 1.1), 2)
            approach_km = round(random.uniform(0.5, 5.0), 2)
            
            actual_duration_min = int(actual_distance_km * random.uniform(1.5, 2.5))
            estimated_duration_min = int(actual_duration_min * random.uniform(0.85, 1.15))
            
            started_at = request_time + timedelta(minutes=random.randint(2, 12))
            completed_at = started_at + timedelta(minutes=actual_duration_min)
            
            # Status
            ride_status = random.choices(statuses, weights=[0.85, 0.15], k=1)[0]
            if ride_status == "CANCELLED":
                started_at_str = ""
                completed_at_str = ""
            else:
                started_at_str = started_at.strftime("%Y-%m-%d %H:%M:%S")
                completed_at_str = completed_at.strftime("%Y-%m-%d %H:%M:%S")
                
            driver = random.choice(driver_pool)
            
            # Compute Fare
            wait_time = max(0, (started_at - request_time).total_seconds() / 60.0) if ride_status == "RIDE_COMPLETED" else 0
            weather_surge = round(random.uniform(1.0, 1.2), 2)
            
            fare_result = compute_fare(
                km=estimated_distance_km,
                is_ac=is_ac,
                trip_type=t_type,
                hour=hour_of_day,
                wait_time_min=wait_time,
                weather_surge=weather_surge
            )
            
            offered_fare = fare_result["offered_fare"]
            final_fare = offered_fare if ride_status == "RIDE_COMPLETED" else ""
            
            revenue_per_km = round(offered_fare / actual_distance_km, 2) if (ride_status == "RIDE_COMPLETED" and actual_distance_km > 0) else ""

            # Geolocation rough estimates
            pickup_lat, pickup_lng = 18.5204 + random.uniform(-0.1, 0.1), 73.8567 + random.uniform(-0.1, 0.1)
            dropoff_lat, dropoff_lng = pickup_lat + random.uniform(-0.2, 0.2), pickup_lng + random.uniform(-0.2, 0.2)
            
            driver_daily_ride_km = round(random.uniform(10.0, 150.0), 2)
            
            writer.writerow({
                "trip_id": trip_id,
                "request_timestamp": request_time.strftime("%Y-%m-%d %H:%M:%S"),
                "started_at": started_at_str,
                "completed_at": completed_at_str,
                "hour_of_day": hour_of_day,
                "day_of_week": day_of_week,
                "is_weekend": is_weekend,
                "is_peak_hour": is_peak_hour,
                "pickup_lat": round(pickup_lat, 6),
                "pickup_lng": round(pickup_lng, 6),
                "dropoff_lat": round(dropoff_lat, 6),
                "dropoff_lng": round(dropoff_lng, 6),
                "approach_km": approach_km,
                "actual_distance_km": actual_distance_km,
                "estimated_distance_km": estimated_distance_km,
                "actual_duration_min": actual_duration_min,
                "estimated_duration_min": estimated_duration_min,
                "vehicle_type": veh_type,
                "trip_type": t_type,
                "offered_fare": offered_fare,
                "final_fare": final_fare,
                "fare_slab_stage_id": random.randint(1, 4),
                "driver_id": driver["id"],
                "driver_rating": driver["rating"],
                "driver_total_trips": driver["total_trips"],
                "driver_shift_hours_elapsed": round(random.uniform(0.5, 12.0), 2),
                "driver_online_minutes": random.randint(30, 720),
                "driver_fuel_level_start": random.choice(fuel_levels),
                "driver_vehicle_condition": random.choice(conditions),
                "driver_daily_ride_km": driver_daily_ride_km,
                "driver_daily_dead_km": round(random.uniform(5.0, 40.0), 2),
                "driver_quota_km": 135.0,
                "driver_overuse_km": max(0.0, driver_daily_ride_km - 135.0),
                "driver_goal_km": driver["goal_km"],
                "driver_goal_km_reached": round(driver_daily_ride_km / driver["goal_km"] * 100, 2),
                "depot_zone": random.choice(cities),
                "rider_acceptance_flag": True if ride_status == "RIDE_COMPLETED" else random.choice([True, False]),
                "first_driver_accepted": random.choice([True, False]),
                "drivers_offered_count": random.randint(1, 5),
                "ride_status": ride_status,
                "revenue_per_km": revenue_per_km
            })
            
            if (i + 1) % 10000 == 0:
                print(f"... generated {i + 1} rows")

    print(f"✅ Successfully wrote {num_rows} rows to {output_path}")

if __name__ == "__main__":
    generate_synthetic_dataset(NUM_ROWS, OUTPUT_FILE)

