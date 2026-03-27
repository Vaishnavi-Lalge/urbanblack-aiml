import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data/processed/processed_data.csv")

MODEL_DIR = os.path.join(BASE_DIR, "model")

# Model output paths
REVENUE_MODEL_PATH = os.path.join(MODEL_DIR, "revenue_model.pkl")
RIDES_MODEL_PATH = os.path.join(MODEL_DIR, "rides_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

# 🚀 UPDATED FEATURES (18 total)
FEATURE_COLUMNS = [
    "hour_of_day",
    "is_peak_hour",
    "is_night_trip",
    "trip_distance",
    "trip_duration_min",
    "surge_multiplier",
    "driver_rating",
    "driver_total_trips",
    "driver_shift_hours_elapsed",
    "total_op_km_today",
    "number_of_rides_in_zone",
    "number_of_active_drivers_in_zone",
    "zone_surge_multiplier",
    "demand_supply_ratio",
    "ride_efficiency",

    # 🔥 NEW STRONG FEATURES
    "avg_speed",
    "rides_per_hour",
    "demand_intensity"
]

# Targets
TARGET_REVENUE = "fare_amount"
TARGET_RIDES = "rides_completed_so_far"