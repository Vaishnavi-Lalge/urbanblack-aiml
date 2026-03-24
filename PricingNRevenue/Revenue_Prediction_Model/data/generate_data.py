import pandas as pd
import numpy as np

np.random.seed(42)

data = []

NUM_DRIVERS = 30       # reduced
NUM_DAYS = 15          # reduced

for driver_id in range(1, NUM_DRIVERS + 1):
    rating = np.random.uniform(3.5, 5.0)
    total_trips = np.random.randint(100, 2000)

    for day in range(NUM_DAYS):
        for hour in range(24):

            # -------------------------------
            # DEMAND (NON-LINEAR)
            # -------------------------------
            if hour in [8, 9, 18, 19, 20]:
                demand_factor = np.random.uniform(1.5, 2.5)
                surge = np.random.uniform(1.2, 1.8)
            else:
                demand_factor = np.random.uniform(0.5, 1.2)
                surge = np.random.uniform(0.8, 1.1)

            # -------------------------------
            # RIDES
            # -------------------------------
            base_rides = np.random.randint(1, 4)
            rides = max(1, int(base_rides * demand_factor))

            # -------------------------------
            # DISTANCE
            # -------------------------------
            avg_km = np.random.uniform(3, 10)
            total_ride_km = rides * avg_km

            dead_km = np.random.uniform(1, 5)
            total_km = total_ride_km + dead_km

            utilization = total_ride_km / total_km if total_km > 0 else 0

            # -------------------------------
            # EXTRA REAL-WORLD FEATURES
            # -------------------------------
            weather_factor = np.random.uniform(0.8, 1.2)   # rain, heat
            traffic_factor = np.random.uniform(0.7, 1.3)   # congestion
            demand_noise = np.random.uniform(0.85, 1.25)

            # Driver skill effect
            rating_factor = 1 + (rating - 4) * 0.15

            # -------------------------------
            # PRICING
            # -------------------------------
            fare_per_km = np.random.uniform(12, 18)

            # -------------------------------
            # NON-LINEAR REVENUE
            # -------------------------------
            revenue = (
                total_ride_km
                * fare_per_km
                * surge
                * rating_factor
                * weather_factor
                * demand_noise
                / traffic_factor
            )

            # Add noise
            revenue += np.random.normal(0, 25)
            revenue = max(0, revenue)

            # -------------------------------
            # SAVE ROW
            # -------------------------------
            data.append([
                driver_id,
                hour,
                day % 7,
                rides,
                total_ride_km,
                total_km,
                dead_km,
                utilization,
                rating,
                total_trips,
                12,
                weather_factor,
                traffic_factor,
                surge,
                revenue,
                rides
            ])

# -------------------------------
# COLUMNS
# -------------------------------
columns = [
    "driver_id", "hour", "day_of_week",
    "rides_count", "total_ride_km", "total_km",
    "dead_km", "utilization",
    "driver_rating", "total_trips", "shift_hours",
    "weather_factor", "traffic_factor", "surge",
    "revenue_per_hour", "rides_per_hour"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("data/dataset.csv", index=False)

print(f"Dataset generated with {len(df)} rows")