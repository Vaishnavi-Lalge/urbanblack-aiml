import joblib
import numpy as np
import os
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")

scaler = joblib.load(SCALER_PATH)
feature_columns = joblib.load(COLUMNS_PATH)


def build_features(input_data: dict):
    try:
        distance = input_data["distance_km"]
        duration = input_data["duration_min"]

        rides_zone = input_data.get("number_of_rides_in_zone", 50)
        drivers_zone = input_data.get("number_of_active_drivers_in_zone", 20)

        # ---------------- FEATURE ENGINEERING ----------------
        demand_supply_ratio = rides_zone / (drivers_zone + 1)
        ride_efficiency = distance / (duration + 1)

        # 🔥 NEW FEATURES
        avg_speed = distance / (duration + 1)
        rides_per_hour = input_data.get("rides_completed_so_far", 5) / (
            input_data.get("driver_shift_hours_elapsed", 6) + 1
        )
        demand_intensity = rides_zone * input_data.get("zone_surge_multiplier", 1.0)

        feature_dict = {
            "hour_of_day": input_data["hour_of_day"],
            "is_peak_hour": int(input_data["hour_of_day"] in [8, 9, 18, 19, 20]),
            "is_night_trip": int(
                input_data["hour_of_day"] >= 22 or input_data["hour_of_day"] <= 5
            ),

            "trip_distance": distance,
            "trip_duration_min": duration,

            "surge_multiplier": input_data.get("surge_multiplier", 1.0),
            "driver_rating": input_data.get("driver_rating", 4.5),
            "driver_total_trips": input_data.get("driver_total_trips", 1000),
            "driver_shift_hours_elapsed": input_data.get("driver_shift_hours_elapsed", 6),

            "total_op_km_today": input_data.get("total_op_km_today", 80),

            "number_of_rides_in_zone": rides_zone,
            "number_of_active_drivers_in_zone": drivers_zone,

            "zone_surge_multiplier": input_data.get("zone_surge_multiplier", 1.0),

            "demand_supply_ratio": demand_supply_ratio,
            "ride_efficiency": ride_efficiency,

            # NEW
            "avg_speed": avg_speed,
            "rides_per_hour": rides_per_hour,
            "demand_intensity": demand_intensity
        }

        # ---------------- ALIGN ----------------
        X = [feature_dict.get(col, 0) for col in feature_columns]

        if len(X) != len(feature_columns):
            raise ValueError(f"Feature mismatch: {len(X)} vs {len(feature_columns)}")

        X = np.array(X).reshape(1, -1)

        X_scaled = scaler.transform(X)

        logger.info(f"✅ Feature vector shape: {X_scaled.shape}")

        return X_scaled, feature_dict

    except Exception as e:
        logger.error(f"❌ Feature pipeline failed: {str(e)}", exc_info=True)
        raise