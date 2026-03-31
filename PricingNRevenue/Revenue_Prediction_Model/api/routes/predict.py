from fastapi import APIRouter
from api.schemas import PredictionRequest

from services.maps_service import get_distance_duration
from services.pricing_service import calculate_price
from features.feature_pipeline import build_features
from explainability.shap_explainer import get_shap_explanation
from monitoring.drift import check_drift
from monitoring.metrics import log_prediction
from monitoring.alerts import check_alerts

from model.load_model import load_models

import numpy as np

router = APIRouter()

# Load models once
revenue_model, rides_model = load_models()


@router.post("/predict")
def predict(data: PredictionRequest):
    try:
        input_data = data.dict()

        # ---------------- MAPS ----------------
        maps = get_distance_duration(
            data.pickup_lat,
            data.pickup_lng,
            data.drop_lat,
            data.drop_lng
        )

        input_data.update(maps)

        # ---------------- FEATURES ----------------
        X_scaled, feature_dict = build_features(input_data)

        # ---------------- REVENUE MODEL ----------------
        log_revenue_pred = float(revenue_model.predict(X_scaled)[0])
        base_revenue_pred = float(np.expm1(log_revenue_pred))  # inverse log

        # ---------------- RIDES MODEL (HYBRID FIX) ----------------
        ml_rides = int(round(rides_model.predict(X_scaled)[0]))

        # rule-based (25 min per ride)
        duration = maps["duration_min"]
        time_based_rides = max(1, int((12 * 60) / (duration + 1)))  # 12 hr shift

        predicted_rides = max(ml_rides, time_based_rides)

        # ---------------- BUSINESS PRICING ----------------
        pricing = calculate_price(
            base_prediction=base_revenue_pred,
            distance_km=maps["distance_km"],
            duration_min=maps["duration_min"],
            total_km_today=data.total_op_km_today,
            surge_multiplier=data.surge_multiplier,
            zone_surge_multiplier=data.zone_surge_multiplier,
            is_night=(data.hour_of_day >= 22 or data.hour_of_day <= 5),
            is_raining=data.is_raining,
            waiting_time_min=data.waiting_time_min
        )

        final_revenue = pricing["final_revenue"]
        final_revenue = max(50, final_revenue)

        # ---------------- RANGES ----------------
        revenue_range = (
            round(final_revenue * 0.9, 2),
            round(final_revenue * 1.1, 2)
        )

        rides_range = (
            max(1, predicted_rides - 1),
            predicted_rides + 1
        )

        # ---------------- CONFIDENCE ----------------
        confidence = round(
            min(0.95, max(0.3, 1 - abs(base_revenue_pred - final_revenue) / (base_revenue_pred + 1))),
            2
        )

        # ---------------- EXPLAINABILITY ----------------
        explanation = get_shap_explanation(X_scaled)

        # ---------------- DRIFT ----------------
        drift = check_drift(feature_dict)

        # ---------------- OUTPUT ----------------
        output = {
            "prediction_status": "success",
            "predicted_revenue": round(final_revenue, 2),
            "predicted_rides": predicted_rides,
            "earnings_range": f"₹{revenue_range[0]} - ₹{revenue_range[1]}",
            "rides_range": f"{rides_range[0]} - {rides_range[1]} rides",
            "confidence": confidence,
            "explainability": explanation,
            "drift": drift
        }

        # ---------------- MONITORING ----------------
        log_prediction(input_data, output)

        alerts = check_alerts(output)
        if alerts:
            output["alerts"] = alerts

        return output

    except Exception as e:
        return {
            "prediction_status": "error",
            "message": str(e)
        }