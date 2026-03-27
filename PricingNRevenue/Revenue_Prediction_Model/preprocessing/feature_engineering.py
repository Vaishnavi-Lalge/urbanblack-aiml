import pandas as pd
from utils.logger import get_logger
from config.settings import IST

logger = get_logger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    try:
        # ---------------- VALIDATION ----------------
        if "timestamp" not in df.columns:
            raise ValueError("❌ 'timestamp' column missing")

        # ---------------- TIME (IST SAFE) ----------------
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        # Convert to IST (important)
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert(IST)

        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek

        # Peak hours
        df["is_peak_hour"] = df["hour"].isin([8, 9, 18, 19, 20]).astype(int)

        # Night trips
        df["is_night"] = ((df["hour"] >= 22) | (df["hour"] <= 5)).astype(int)

        # ---------------- DRIVER RULES ----------------

        # Expected rides (25 min rule)
        df["expected_rides"] = (12 * 60) / 25  # ~28 rides

        # KM target
        df["km_target"] = 135

        # Extra KM
        df["extra_km"] = (df["total_op_km_today"] - 135).clip(lower=0)

        # Bonus ₹12/km
        df["extra_bonus"] = df["extra_km"] * 12

        # ---------------- PRICING FEATURES ----------------

        df["calculated_base_fare"] = 55
        df["calculated_km_fare"] = df["trip_distance"] * 25

        # Night charge (safe)
        df["night_charge"] = df["fare_amount"] * 0.25 * df["is_night"]

        # ---------------- DEMAND FEATURES ----------------

        df["demand_supply_ratio"] = (
            df["number_of_rides_in_zone"] /
            (df["number_of_active_drivers_in_zone"] + 1)
        )

        # ---------------- EXTRA FEATURES (INDUSTRY BOOST) ----------------

        # Avg speed (km/min)
        df["avg_speed"] = df["trip_distance"] / (df["trip_duration_min"] + 1)

        # Rides per hour
        df["rides_per_hour"] = df["rides_completed_so_far"] / (
            df["driver_shift_hours_elapsed"] + 1
        )

        # Demand intensity
        df["demand_intensity"] = (
            df["number_of_rides_in_zone"] * df.get("zone_surge_multiplier", 1)
        )

        logger.info("✅ Feature engineering completed successfully")

        return df

    except Exception as e:
        logger.error(f"❌ Feature engineering failed: {str(e)}", exc_info=True)
        raise