import os

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

from src.decision_logic import default_decision_config, evaluate_decision, is_model_source
from src.feature_engineering import engineer_features

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
RULE_MIN_CONFIDENCE = 0.70

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run src/train.py first.")

app = FastAPI()
artifact = joblib.load(MODEL_PATH)

if isinstance(artifact, dict) and "model" in artifact:
    model = artifact["model"]
    MODEL_FEATURES = artifact["model_features"]
    DECISION_CONFIG = artifact.get("decision_config", default_decision_config())
else:
    model = artifact
    MODEL_FEATURES = list(model.named_steps["prep"].feature_names_in_)
    DECISION_CONFIG = default_decision_config()


class InputData(BaseModel):
    city: str
    segment_start_timestamp: str
    segment_end_timestamp: str
    latitude: float
    longitude: float
    speed_kmh: float
    heading_degrees: float
    gps_accuracy_meters: float
    total_distance_km: float
    avg_speed_kmh: float
    max_speed_kmh: float
    speed_std_dev: float
    heading_variance: float
    ping_count: int
    duration_seconds: float
    is_near_accepted_pickup: bool
    road_speed_limit_kmh: float
    speed_vs_road_limit_ratio: float
    zone_id: str
    hour_of_day: int
    driver_shift_hours_elapsed: float
    time_since_last_trip_end_min: float
    consecutive_operational_segments_count: int


def build_model_frame(row: dict) -> pd.DataFrame:
    engineered = engineer_features(pd.DataFrame([row]))
    return engineered[MODEL_FEATURES].copy()


def decision_engine(row: dict, proba: float) -> tuple[int, str]:
    decision = evaluate_decision(row, proba, DECISION_CONFIG)
    return decision["prediction"], decision["source"]


def get_source_type(source: str) -> str:
    return "model" if is_model_source(source) else "rule"


def get_response_confidence(proba: float, source: str) -> float:
    if get_source_type(source) == "rule":
        return max(float(proba), RULE_MIN_CONFIDENCE)
    return float(proba)


def generate_reason(row: dict, decision: dict, proba: float) -> str:
    source = decision["source"]

    if source == "rule_waiting_active":
        return "Driver is stationary but highly active with recent engagement."

    if source == "rule_high_activity":
        return "High speed and long distance indicate operational activity."

    if source == "model_high_conf_positive":
        return "Model detected a strong operational activity pattern."

    if source == "model_high_conf_negative":
        return "Model detected a strong non-operational inactivity pattern."

    if source == "soft_rule_adjusted":
        if decision["prediction"] == 1:
            return "Borderline model output was nudged operational by supporting activity signals."
        return "Borderline model output was nudged non-operational by inactivity signals."

    if row.get("time_since_last_trip_end_min", 0) > 20:
        return "Recent inactivity outweighs movement context."

    if row.get("speed_kmh", 0) > 12 and row.get("ping_count", 0) > 50:
        return "Sustained movement and activity indicate operational behavior."

    if decision["prediction"] == 1:
        return f"Model-based operational decision at confidence {proba:.3f}."

    return f"Model-based non-operational decision at confidence {proba:.3f}."


@app.post("/predict")
def predict(data: InputData):
    row = data.model_dump()
    model_frame = build_model_frame(row)
    proba = float(model.predict_proba(model_frame)[0][1])
    decision = evaluate_decision(row, proba, DECISION_CONFIG)
    response_confidence = get_response_confidence(proba, decision["source"])
    source_type = get_source_type(decision["source"])
    reason = generate_reason(row, decision, response_confidence)

    return {
        "prediction": int(decision["prediction"]),
        "label": "Operational" if decision["prediction"] == 1 else "Non-Operational",
        "confidence": round(response_confidence, 3),
        "decision_score": round(decision["decision_score"], 3),
        "source": decision["source"],
        "source_type": source_type,
        "reason": reason,
        "adjustments": decision["adjustments"],
        "total_adjustment": round(decision["total_adjustment"], 3),
    }
