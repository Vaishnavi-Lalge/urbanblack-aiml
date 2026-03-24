import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os

def preprocess_data(target="revenue_per_hour"):
    """
    Preprocess dataset and return features + target

    target:
        "revenue_per_hour"  -> for revenue model
        "rides_per_hour"    -> for rides model
    """

    # -------------------------------
    # LOAD DATA
    # -------------------------------
    df = pd.read_csv("data/dataset.csv")

    # Handle missing values
    df = df.fillna(0)

    # -------------------------------
    # DEFINE TARGET
    # -------------------------------
    if target not in ["revenue_per_hour", "rides_per_hour"]:
        raise ValueError("Invalid target. Choose 'revenue_per_hour' or 'rides_per_hour'")

    y = df[target]

    # -------------------------------
    # REMOVE DATA LEAKAGE
    # -------------------------------
    X = df.drop(["revenue_per_hour", "rides_per_hour"], axis=1)

    # -------------------------------
    # FEATURE ORDER (IMPORTANT)
    # Must match feature_pipeline.py
    # -------------------------------
    feature_cols = [
        "driver_id",
        "hour",
        "day_of_week",
        "rides_count",
        "total_ride_km",
        "total_km",
        "dead_km",
        "utilization",
        "driver_rating",
        "total_trips",
        "shift_hours",
        "weather_factor",
        "traffic_factor",
        "surge"
    ]

    X = X[feature_cols]

    # -------------------------------
    # SCALING
    # -------------------------------
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Save scaler (used in API)
    os.makedirs("model", exist_ok=True)
    joblib.dump(scaler, "model/scaler.pkl")

    return X_scaled, y