import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config.settings import MODEL_DIR


def preprocess_data(df):

    # ---------------- VALIDATION ----------------
    required_cols = [
        "hour_of_day",
        "trip_distance",
        "trip_duration_min",
        "fare_amount",
        "rides_completed_so_far",
        "number_of_rides_in_zone",
        "number_of_active_drivers_in_zone",
        "total_op_km_today"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"❌ Missing column: {col}")

    # ---------------- CLEAN ----------------
    df = df.drop_duplicates()
    df = df.ffill().bfill()

    # ---------------- FEATURE ENGINEERING ----------------

    # Peak hour
    df["is_peak_hour"] = df["hour_of_day"].isin([8, 9, 18, 19, 20]).astype(int)

    # Night trip
    df["is_night_trip"] = ((df["hour_of_day"] >= 22) | (df["hour_of_day"] <= 5)).astype(int)

    # Demand-Supply Ratio
    df["demand_supply_ratio"] = (
        df["number_of_rides_in_zone"] /
        (df["number_of_active_drivers_in_zone"] + 1)
    )

    # Ride Efficiency
    df["ride_efficiency"] = df["trip_distance"] / (df["trip_duration_min"] + 1)

    # 🔥 NEW FEATURES
    df["avg_speed"] = df["trip_distance"] / (df["trip_duration_min"] + 1)
    df["rides_per_hour"] = df["rides_completed_so_far"] / (df["driver_shift_hours_elapsed"] + 1)
    df["demand_intensity"] = df["number_of_rides_in_zone"] * df["zone_surge_multiplier"]

    # Bonus logic
    df["extra_km"] = (df["total_op_km_today"] - 135).clip(lower=0)
    df["extra_bonus"] = df["extra_km"] * 12

    # ---------------- SAVE PROCESSED DATA ----------------
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/processed_data.csv", index=False)

    print("✅ Processed dataset saved")

    # ---------------- FEATURES (MATCH CONFIG) ----------------
    features = [
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

        # NEW
        "avg_speed",
        "rides_per_hour",
        "demand_intensity"
    ]

    for col in features:
        if col not in df.columns:
            raise ValueError(f"❌ Feature missing: {col}")

    X = df[features]

    # ---------------- SCALER ----------------
    scaler = StandardScaler()
    scaler.fit(X)

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
    joblib.dump(features, f"{MODEL_DIR}/columns.pkl")

    print(f"✅ Artifacts saved ({len(features)} features)")

    return df