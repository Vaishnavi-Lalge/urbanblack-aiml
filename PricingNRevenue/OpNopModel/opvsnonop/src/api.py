import os
from collections import defaultdict

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.db import create_tables, get_driver_summary, insert_segment, segment_exists, update_summary
from src.decision_logic import default_decision_config, evaluate_decision, is_model_source
from src.feature_engineering import engineer_features

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
RULE_MIN_CONFIDENCE = 0.70

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run src/train.py first.")

app = FastAPI()
create_tables()
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


class AggregateSegmentInput(InputData):
    segment_id: str
    driver_id: str


class DriverBatchRequest(BaseModel):
    segments: list[AggregateSegmentInput]


def build_model_frame(row: dict) -> pd.DataFrame:
    engineered = engineer_features(pd.DataFrame([row]))
    return engineered[MODEL_FEATURES].copy()


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


def format_hours(hours_float: float) -> str:
    total_minutes = max(0, int(round(float(hours_float) * 60)))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours}h {minutes}m"


def build_hours_summary(operational_hours: float, non_operational_hours: float) -> dict:
    return {
        "operational": format_hours(operational_hours),
        "non_operational": format_hours(non_operational_hours),
        "operational_hours": round(float(operational_hours), 4),
        "non_operational_hours": round(float(non_operational_hours), 4),
    }


def build_hours_summary_from_seconds(operational_seconds: int, non_operational_seconds: int) -> dict:
    return build_hours_summary(
        float(operational_seconds) / 3600.0,
        float(non_operational_seconds) / 3600.0,
    )


def get_segment_hours(duration_seconds: float, prediction: int) -> dict:
    duration_seconds = max(0.0, float(duration_seconds))
    operational_seconds = duration_seconds if int(prediction) == 1 else 0.0
    non_operational_seconds = duration_seconds if int(prediction) == 0 else 0.0
    summary = build_hours_summary_from_seconds(operational_seconds, non_operational_seconds)
    summary["segment_duration"] = format_hours(duration_seconds / 3600.0)
    summary["segment_duration_hours"] = round(duration_seconds / 3600.0, 4)
    return summary


def predict_row(row: dict) -> dict:
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
        "hours": get_segment_hours(row.get("duration_seconds", 0.0), decision["prediction"]),
        "adjustments": decision["adjustments"],
        "total_adjustment": round(decision["total_adjustment"], 3),
    }


@app.post("/predict")
def predict(data: InputData):
    return predict_row(data.model_dump())


@app.post("/aggregate-hours")
def aggregate_hours(data: DriverBatchRequest):
    if not data.segments:
        raise HTTPException(status_code=400, detail="At least one segment is required.")

    total_processed_segments = 0
    total_skipped_segments = 0
    invalid_segments = []
    driver_batches: dict[str, dict] = defaultdict(
        lambda: {
            "processed_segments": 0,
            "skipped_segments": 0,
            "batch_operational_seconds": 0,
            "batch_non_operational_seconds": 0,
            "segment_results": [],
        }
    )

    for segment in data.segments:
        row = segment.model_dump()
        driver_id = row["driver_id"].strip()
        segment_id = row["segment_id"].strip()
        duration_seconds = int(round(float(row.get("duration_seconds", 0))))

        if not driver_id:
            total_skipped_segments += 1
            invalid_segments.append(
                {
                    "segment_id": segment_id,
                    "status": "skipped",
                    "reason": "Missing driver_id",
                }
            )
            continue

        batch = driver_batches[driver_id]

        if not segment_id:
            total_skipped_segments += 1
            batch["skipped_segments"] += 1
            batch["segment_results"].append(
                {
                    "segment_id": "",
                    "status": "skipped",
                    "reason": "Missing segment_id",
                }
            )
            continue

        if duration_seconds <= 0:
            total_skipped_segments += 1
            batch["skipped_segments"] += 1
            batch["segment_results"].append(
                {
                    "segment_id": segment_id,
                    "status": "skipped",
                    "reason": "Invalid duration_seconds",
                }
            )
            continue

        if segment_exists(segment_id):
            total_skipped_segments += 1
            batch["skipped_segments"] += 1
            batch["segment_results"].append(
                {
                    "segment_id": segment_id,
                    "status": "duplicate",
                    "reason": "Segment already processed",
                }
            )
            continue

        prediction = predict_row(row)
        inserted = insert_segment(
            {
                "segment_id": segment_id,
                "driver_id": driver_id,
                "start_time": row["segment_start_timestamp"],
                "end_time": row["segment_end_timestamp"],
                "duration_seconds": duration_seconds,
                "prediction": prediction["prediction"],
                "confidence": prediction["confidence"],
                "source": prediction["source"],
            }
        )

        if not inserted:
            total_skipped_segments += 1
            batch["skipped_segments"] += 1
            batch["segment_results"].append(
                {
                    "segment_id": segment_id,
                    "status": "duplicate",
                    "reason": "Segment already processed",
                }
            )
            continue

        update_summary(driver_id, duration_seconds, prediction["prediction"])

        if prediction["prediction"] == 1:
            batch["batch_operational_seconds"] += duration_seconds
        else:
            batch["batch_non_operational_seconds"] += duration_seconds
        total_processed_segments += 1
        batch["processed_segments"] += 1

        batch["segment_results"].append(
            {
                "segment_id": segment_id,
                "status": "processed",
                "label": prediction["label"],
                "confidence": prediction["confidence"],
                "source": prediction["source"],
                "source_type": prediction["source_type"],
                "hours": prediction["hours"],
            }
        )

    drivers = {}
    for driver_id, batch in driver_batches.items():
        lifetime_seconds = get_driver_summary(driver_id) or {
            "operational_seconds": 0,
            "non_operational_seconds": 0,
        }
        drivers[driver_id] = {
            "current_batch": build_hours_summary_from_seconds(
                batch["batch_operational_seconds"],
                batch["batch_non_operational_seconds"],
            ),
            "lifetime": build_hours_summary_from_seconds(
                lifetime_seconds["operational_seconds"],
                lifetime_seconds["non_operational_seconds"],
            ),
            "processed_segments": batch["processed_segments"],
            "skipped_segments": batch["skipped_segments"],
            "segment_results": batch["segment_results"],
        }

    response = {
        "drivers": drivers,
        "processed_segments": total_processed_segments,
        "skipped_segments": total_skipped_segments,
    }

    if invalid_segments:
        response["invalid_segments"] = invalid_segments

    if len(drivers) == 1:
        only_driver_id, only_driver_result = next(iter(drivers.items()))
        response["driver_id"] = only_driver_id
        response["current_batch"] = only_driver_result["current_batch"]
        response["lifetime"] = only_driver_result["lifetime"]
        response["segment_results"] = only_driver_result["segment_results"]

    return response