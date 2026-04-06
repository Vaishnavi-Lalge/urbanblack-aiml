"""
IMPROVED PREDICTION ROUTE - Production Ready

Key Improvements:
1. Uses rides_per_hour model (not cumulative rides)
2. Converts predictions back with realistic constraints
3. Data-driven confidence calculation
4. Better rides range calculation
5. Explainability and monitoring integrated
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
import numpy as np
import joblib
from pathlib import Path

from api.schemas import PredictionRequest, PredictionResponse
from services.maps_service import get_distance_duration
from services.pricing_service import calculate_price
from services.confidence_calculator import ConfidenceCalculator, calculate_final_confidence
from explainability.shap_explainer import get_shap_explanation
from monitoring.drift import check_drift
from monitoring.metrics import log_prediction
from monitoring.alerts import check_alerts

from model.load_model import load_models


router = APIRouter()

# Global model cache
_models_cache = None
_scaler_cache = None
_features_cache = None
_confidence_calc_cache = None


def get_models_and_scaler():
    """Load models and scaler (cached)."""
    global _models_cache, _scaler_cache, _features_cache, _confidence_calc_cache
    
    if _models_cache is None:
        print("📦 Loading models...")
        _models_cache = load_models()  # Returns (revenue_model, rides_model)
        
        model_dir = Path("model")
        _scaler_cache = joblib.load(model_dir / "scaler.pkl")
        _features_cache = joblib.load(model_dir / "columns.pkl")
        _confidence_calc_cache = ConfidenceCalculator()
    
    return _models_cache, _scaler_cache, _features_cache, _confidence_calc_cache


def build_feature_vector(input_dict: Dict) -> np.ndarray:
    """
    Build scaled feature vector from input.
    
    Matches the feature columns used during training.
    """
    models, scaler, features, _ = get_models_and_scaler()
    
    # Extract features in correct order
    feature_values = []
    for feature_name in features:
        if feature_name in input_dict:
            feature_values.append(input_dict[feature_name])
        else:
            # Use safe default for missing features
            feature_values.append(0)
    
    # Scale
    feature_array = np.array([feature_values])
    feature_scaled = scaler.transform(feature_array)
    
    return feature_scaled[0], np.array(feature_values)


def predict_rides_realistic(
    rides_per_hour_prediction: float,
    driver_shift_hours: float,
    trip_duration: float,
    demand_supply_ratio: float,
    surge_multiplier: float
) -> int:
    """
    Convert rides_per_hour prediction to realistic rides count.
    
    CRITICAL FIX: This is how we prevent unrealistic outputs like 150 rides.
    
    Args:
        rides_per_hour_prediction: Model's rides_per_hour prediction
        driver_shift_hours: How many hours driver is working
        trip_duration: Average trip duration in minutes
        demand_supply_ratio: Rides vs drivers
        surge_multiplier: Current surge
    
    Returns:
        Realistic rides count (typically 1-35 per shift)
    """
    
    # ===== BASE CALCULATION =====
    # rides_per_hour * shift_hours
    base_rides = rides_per_hour_prediction * max(1, driver_shift_hours)
    
    # ===== ADJUST FOR CONTEXT =====
    
    # Long trips → fewer rides (can't do as many)
    if trip_duration > 30:
        base_rides *= 0.7  # 30% reduction for long trips
    elif trip_duration > 60:
        base_rides *= 0.5  # 50% reduction for very long trips
    
    # High demand → more rides (faster turnover)
    if demand_supply_ratio > 2.0:
        base_rides *= 1.2
    elif demand_supply_ratio > 3.0:
        base_rides *= 1.3  # Cap at 1.3x
    
    # Surge effect → more rides (drivers work harder)
    if surge_multiplier > 1.5:
        base_rides *= 1.1  # 10% more for surge
    
    # ===== APPLY CONSTRAINTS =====
    
    # Minimum: 1 ride
    rides = max(1, base_rides)
    
    # Maximum: realistic maximum
    # Typical: 20-35 rides per 12-hour shift
    # That's 1.67-2.92 rides per hour
    # For shorter shifts (8 hours): 1.67-2.92 rides per hour = 13-23 rides
    max_realistic = 3.5 * driver_shift_hours  # ~3.5 rides/hour max
    rides = min(rides, max_realistic)
    
    # Cap hard maximums
    if driver_shift_hours <= 4:
        rides = min(rides, 12)  # Short shift
    elif driver_shift_hours <= 8:
        rides = min(rides, 20)  # Medium shift
    elif driver_shift_hours <= 12:
        rides = min(rides, 30)  # Long shift
    else:
        rides = min(rides, 35)  # Full day
    
    return int(np.round(rides))


@router.post("/api/v3/predict", response_model=Dict)
def predict_improved(data: PredictionRequest):
    """
    Improved prediction endpoint with realistic outputs and data-driven confidence.
    
    Key Improvements:
    1. ✅ Rides predicted as ride_per_hour → converted to realistic rides
    2. ✅ Confidence is data-driven from multiple signals
    3. ✅ Better range calculation based on confidence
    4. ✅ Explainability and monitoring integrated
    """
    
    try:
        print(f"\n🔮 Prediction request from {data.pickup_lat}, {data.pickup_lng}")
        
        # Load models
        models, scaler, features, confidence_calc = get_models_and_scaler()
        revenue_model, rides_model = models
        
        # Convert request to dict
        input_data = data.dict()
        
        # ===== GET MAPS DATA =====
        try:
            maps = get_distance_duration(
                data.pickup_lat,
                data.pickup_lng,
                data.drop_lat,
                data.drop_lng
            )
            input_data.update(maps)
        except Exception as e:
            print(f"⚠️ Maps error: {e}")
            maps = {
                "distance_km": 5.0,
                "duration_min": 15.0,
                "distance_text": "Unknown",
                "duration_text": "Unknown"
            }
            input_data.update(maps)
        
        # ===== BUILD FEATURES =====
        features_scaled, features_raw = build_feature_vector(input_data)
        features_scaled = np.array([features_scaled])
        
        # ===== REVENUE PREDICTION =====
        log_revenue_pred = float(revenue_model.predict(features_scaled)[0])
        ml_revenue_pred = float(np.expm1(log_revenue_pred))  # Inverse log
        ml_revenue_pred = max(50, ml_revenue_pred)  # Minimum fare
        
        # ===== RIDES PREDICTION (NEW LOGIC!) =====
        # Model predicts rides_per_hour
        rides_per_hour_raw = float(rides_model.predict(features_scaled)[0])
        rides_per_hour_raw = np.clip(rides_per_hour_raw, 0.1, 4.0)  # Bound
        
        # Convert to realistic rides count
        predicted_rides = predict_rides_realistic(
            rides_per_hour_prediction=rides_per_hour_raw,
            driver_shift_hours=max(1, data.driver_shift_hours_elapsed),
            trip_duration=maps["duration_min"],
            demand_supply_ratio=data.number_of_rides_in_zone / (data.number_of_active_drivers_in_zone + 1),
            surge_multiplier=data.surge_multiplier * (data.zone_surge_multiplier or 1.0)
        )
        
        print(f"   Rides/hour model: {rides_per_hour_raw:.2f} → Final rides: {predicted_rides}")
        
        # ===== BUSINESS LOGIC PRICING =====
        pricing = calculate_price(
            base_prediction=ml_revenue_pred,
            distance_km=maps["distance_km"],
            duration_min=maps["duration_min"],
            total_km_today=data.total_op_km_today,
            surge_multiplier=data.surge_multiplier,
            zone_surge_multiplier=data.zone_surge_multiplier or 1.0,
            is_night=(data.hour_of_day >= 22 or data.hour_of_day <= 5),
            is_raining=data.is_raining,
            waiting_time_min=data.waiting_time_min or 0
        )
        
        final_revenue = pricing["final_revenue"]
        
        # ===== DATA-DRIVEN CONFIDENCE =====
        is_peak = data.hour_of_day in [8, 9, 12, 13, 18, 19, 20]
        is_night = data.hour_of_day >= 22 or data.hour_of_day <= 5
        demand_supply = data.number_of_rides_in_zone / (data.number_of_active_drivers_in_zone + 1)
        
        confidence, confidence_breakdown = calculate_final_confidence(
            ml_revenue=ml_revenue_pred,
            business_logic_revenue=final_revenue,
            features_dict=input_data,
            features_array=features_raw,
            is_peak=is_peak,
            is_night=is_night,
            demand_supply_ratio=demand_supply,
            surge=data.surge_multiplier,
            duration=maps["duration_min"]
        )
        
        print(f"   Confidence: {confidence:.1%}")
        
        # ===== PRICE RANGE (based on confidence) =====
        min_price, max_price, range_pct = confidence_calc.calculate_price_range(final_revenue, confidence)
        
        # ===== RIDES RANGE =====
        rides_min = max(1, predicted_rides - 1)
        rides_max = predicted_rides + 1
        
        # ===== EXPLAINABILITY =====
        try:
            explanation = get_shap_explanation(features_scaled)
        except:
            explanation = []
        
        # ===== DRIFT DETECTION =====
        try:
            drift_info = check_drift(input_data)
        except:
            drift_info = {}
        
        # ===== LOGGING =====
        try:
            log_prediction({
                "input": input_data,
                "output": {
                    "revenue": final_revenue,
                    "rides": predicted_rides,
                    "confidence": confidence
                }
            })
        except:
            pass
        
        # ===== ALERTS =====
        try:
            check_alerts({
                "revenue": final_revenue,
                "rides": predicted_rides,
                "confidence": confidence
            })
        except:
            pass
        
        # ===== RESPONSE =====
        response = {
            "prediction_status": "success",
            "predicted_revenue": round(final_revenue, 2),
            "predicted_rides": predicted_rides,
            "rides_per_hour": round(rides_per_hour_raw, 2),
            "min_price": round(min_price, 2),
            "max_price": round(max_price, 2),
            "earnings_range": f"₹{min_price:.0f} - ₹{max_price:.0f}",
            "rides_range": f"{rides_min} - {rides_max} rides",
            "confidence": round(confidence, 3),
            "confidence_breakdown": confidence_breakdown,
            "trip_details": {
                "distance_km": round(maps["distance_km"], 2),
                "duration_min": round(maps["duration_min"], 1),
                "avg_speed": round(maps["distance_km"] / (maps["duration_min"] / 60 + 1), 1)
            },
            "model_predictions": {
                "ml_revenue": round(ml_revenue_pred, 2),
                "business_logic_revenue": round(final_revenue, 2),
                "agreement_percent": round(100 * (1 - abs(ml_revenue_pred - final_revenue) / (final_revenue + 1)), 1)
            },
            "explainability": explanation[:5],  # Top 5 factors
            "drift": drift_info
        }
        
        print(f"   ✅ Response: ₹{final_revenue}, {predicted_rides} rides, {confidence:.0%} confidence\n")
        
        return response
    
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v3/info")
def get_info():
    """Get system information."""
    models, scaler, features, _ = get_models_and_scaler()
    
    return {
        "system": "Improved Revenue & Rides Prediction (v3)",
        "improvements": [
            "✅ Rides_per_hour target (not cumulative)",
            "✅ Realistic rides constraints (1-35 per shift)",
            "✅ Data-driven confidence (0.5-0.95)",
            "✅ Better feature engineering",
            "✅ Input quality scoring",
            "✅ Data drift detection"
        ],
        "features": len(features),
        "endpoint": "/api/v3/predict (POST)"
    }

