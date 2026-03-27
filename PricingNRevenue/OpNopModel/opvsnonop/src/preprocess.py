import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_PATH = os.path.join(DATA_DIR, "OPERATIONAL VS NON-OPERATIONAL KM CLASSIFIER.csv")
OUT_PATH = os.path.join(DATA_DIR, "clean_data.csv")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.feature_engineering import engineer_features


def clean_data():
    df = pd.read_csv(DATA_PATH)

    # Normalize label values from the source CSV before mapping to binary.
    df["label"] = (
        df["label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "operational": 1,
                "non_operational": 0,
                "non-operational": 0,
            }
        )
    )

    df = df[df["label"].isin([0, 1])].copy()
    df["label"] = df["label"].astype(int)

    drop_cols = [
        "trip_phase",
        "app_status",
        "dominant_app_status",
        "reposition_instruction_id",
        "trip_id",
        "segment_id",
        "driver_id",
        "labeling_method",
        "consecutive_operational_segments_count",
        "gps_accuracy_meters",
        "heading_variance",
        "is_near_accepted_pickup",
        "duration_seconds",
        "speed_std_dev",
        "avg_speed_kmh",
        "max_speed_kmh",
        "total_distance_km",
        "speed_vs_road_limit_ratio",
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    df = engineer_features(df)

    df = df.dropna().drop_duplicates()

    print("\nFinal Shape:", df.shape)
    print("\nLabel Distribution:\n", df["label"].value_counts())

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print("\nClean data saved.")


if __name__ == "__main__":
    clean_data()
