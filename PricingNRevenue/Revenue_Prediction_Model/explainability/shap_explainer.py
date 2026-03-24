import shap
import numpy as np
import joblib

model = joblib.load("model/revenue_model_v1.pkl")

explainer = shap.Explainer(model)

# ✅ FIXED: 14 FEATURES
FEATURE_NAMES = [
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

def get_shap_values(features):
    try:
        shap_values = explainer(features)

        result = []

        # ✅ SAFE LOOP
        for i, val in enumerate(shap_values.values[0][:len(FEATURE_NAMES)]):
            result.append({
                "feature": FEATURE_NAMES[i],
                "impact": float(val)
            })

        result = sorted(result, key=lambda x: abs(x["impact"]), reverse=True)

        return result[:5]

    except Exception as e:
        return [{"error": str(e)}]