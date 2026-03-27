import os
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "processed_data.csv")


# ---------------- LOAD REFERENCE STATS ----------------
def load_reference_stats():
    try:
        df = pd.read_csv(DATA_PATH)

        stats = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats[col] = {
                    "mean": df[col].mean(),
                    "std": df[col].std() + 1e-6  # avoid division by zero
                }

        logger.info("📊 Reference stats loaded for drift detection")

        return stats

    except Exception as e:
        logger.error(f"❌ Failed to load reference stats: {str(e)}")
        return {}


# Load once (startup optimization)
reference_stats = load_reference_stats()


# ---------------- DRIFT CHECK ----------------
def check_drift(input_features: dict, threshold=2.5):
    try:
        drift_report = {}

        for feature, value in input_features.items():
            if feature not in reference_stats:
                continue

            mean = reference_stats[feature]["mean"]
            std = reference_stats[feature]["std"]

            z_score = (value - mean) / std

            drift = abs(z_score) > threshold

            drift_report[feature] = {
                "value": float(value),
                "z_score": float(round(z_score, 4)),
                "drift": bool(drift)
            }

        return drift_report

    except Exception as e:
        logger.error(f"❌ Drift detection failed: {str(e)}", exc_info=True)
        return {}