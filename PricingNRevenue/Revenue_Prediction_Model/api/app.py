import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from api.schemas import PredictionRequest
from model.load_model import load_models
from features.feature_pipeline import build_features
from utils.logger import get_logger

# Safe SHAP import
try:
    from explainability.shap_explainer import get_shap_values
    SHAP_AVAILABLE = True
except:
    SHAP_AVAILABLE = False

from monitoring.metrics import log_prediction, get_metrics
from monitoring.drift import detect_drift

import numpy as np

app = FastAPI(title="Revenue + Rides Prediction API", version="6.0")

logger = get_logger()

# -------------------------------
# LOAD MODELS (SAFE)
# -------------------------------
try:
    revenue_model, rides_model = load_models()
    MODELS_LOADED = True
except Exception as e:
    logger.error(f"Model loading failed: {str(e)}")
    MODELS_LOADED = False


# -------------------------------
# FEATURE NAMES
# -------------------------------
FEATURE_NAMES = [
    "driver_id", "hour", "day_of_week", "rides_count",
    "total_ride_km", "total_km", "dead_km", "utilization",
    "driver_rating", "total_trips", "shift_hours",
    "weather_factor", "traffic_factor", "surge"
]


# -------------------------------
# SAFE SERIALIZER
# -------------------------------
def to_python(obj):
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python(i) for i in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj


# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.get("/")
def health():
    return {
        "status": "healthy",
        "models_loaded": MODELS_LOADED,
        "version": "6.0"
    }


# -------------------------------
# METRICS
# -------------------------------
@app.get("/metrics")
def metrics():
    try:
        return to_python(get_metrics())
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# -------------------------------
# FALLBACK EXPLAINABILITY
# -------------------------------
def fallback_explainability(features):
    try:
        importances = revenue_model.feature_importances_

        explanation = []
        for i, imp in enumerate(importances[:len(FEATURE_NAMES)]):
            explanation.append({
                "feature": FEATURE_NAMES[i],
                "importance": float(imp),
                "value": float(features[0][i])
            })

        explanation = sorted(explanation, key=lambda x: x["importance"], reverse=True)
        return explanation[:5]

    except Exception:
        return []


# -------------------------------
# PREDICT
# -------------------------------
@app.post("/predict")
def predict(request: PredictionRequest):

    # -------------------------------
    # MODEL CHECK
    # -------------------------------
    if not MODELS_LOADED:
        return {
            "prediction_status": "failed",
            "error": "Models not loaded"
        }

    try:
        logger.info(f"Prediction request for driver {request.driver_id}")

        # -------------------------------
        # FEATURE ENGINEERING
        # -------------------------------
        scaled_features, raw_features = build_features(request)

        # -------------------------------
        # MODEL PREDICTIONS
        # -------------------------------
        predicted_revenue = float(revenue_model.predict(scaled_features)[0])
        predicted_rides = float(rides_model.predict(scaled_features)[0])

        # -------------------------------
        # ROUNDING
        # -------------------------------
        predicted_revenue = round(predicted_revenue, 2)
        predicted_rides = max(1, int(round(predicted_rides)))

        # -------------------------------
        # RANGES
        # -------------------------------
        min_rev = round(predicted_revenue * 0.9, 2)
        max_rev = round(predicted_revenue * 1.1, 2)

        min_rides = max(1, int(predicted_rides * 0.85))
        max_rides = int(predicted_rides * 1.15)

        earnings_range = f"₹{min_rev} - ₹{max_rev}"
        rides_range = f"{min_rides} - {max_rides} rides"

        # -------------------------------
        # CONFIDENCE
        # -------------------------------
        confidence = round(
            max(0.6, min(1.0, 1 - abs(predicted_revenue - 500) / 1000)),
            2
        )

        # -------------------------------
        # EXPLAINABILITY
        # -------------------------------
        if SHAP_AVAILABLE:
            try:
                explanation = get_shap_values(scaled_features)
            except Exception as e:
                logger.warning(f"SHAP failed: {str(e)}")
                explanation = fallback_explainability(scaled_features)
        else:
            explanation = fallback_explainability(scaled_features)

        # -------------------------------
        # DRIFT DETECTION
        # -------------------------------
        try:
            drift_report = detect_drift([raw_features])
        except Exception as e:
            logger.warning(f"Drift detection failed: {str(e)}")
            drift_report = {}

        # -------------------------------
        # MONITORING
        # -------------------------------
        try:
            log_prediction({
                "input": request.dict(),
                "predicted_revenue": predicted_revenue,
                "predicted_rides": predicted_rides
            })
        except Exception as e:
            logger.warning(f"Logging failed: {str(e)}")

        # -------------------------------
        # FINAL RESPONSE
        # -------------------------------
        response = {
            "prediction_status": "success",
            "predicted_revenue": predicted_revenue,
            "predicted_rides": predicted_rides,
            "earnings_range": earnings_range,
            "rides_range": rides_range,
            "confidence": confidence,
            "explainability": explanation,
            "drift": drift_report
        }

        return to_python(response)

    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")

        return {
            "prediction_status": "failed",
            "error": str(e)
        }