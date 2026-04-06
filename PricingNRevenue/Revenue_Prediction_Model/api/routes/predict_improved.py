"""
IMPROVED PREDICTION ROUTE

Key improvements:
1. Uses centralized feature engineering (no mismatch)
2. Better business logic (realistic Uber/Ola pricing)
3. Weighted blend of ML + business logic (not 90/10)
4. Better rides prediction (not just max)
5. Meaningful confidence scoring
6. Better explainability (business context)
7. Production-grade error handling
"""

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import numpy as np
from api.schemas import PredictionRequest
from services.maps_service import get_distance_duration
from services.pricing_logic import (
    calculate_realistic_revenue,
    calculate_confidence_score,
    apply_surge_saturation
)
from features.inference_pipeline import (
    build_inference_features,
    get_model_predictions,
    sanity_check_prediction
)
from explainability.shap_explainer import get_shap_explanation
from monitoring.drift import check_drift
from monitoring.metrics import log_prediction
from monitoring.alerts import check_alerts
from model.load_model import load_models
from utils.logger import get_logger
import json

logger = get_logger(__name__)

router = APIRouter()

# Load models once (efficient)
revenue_model, rides_model = load_models()

# ============================================================================
# CONSTANTS
# ============================================================================

# ML model influence weight (increased from 0.1 to 0.25-0.35)
# This means: 65-75% business logic + 25-35% ML
ML_WEIGHT_REVENUE = 0.30  # 30% ML, 70% business logic

ML_WEIGHT_RIDES = 0.40    # 40% ML, 60% time-based rule


# ============================================================================
# HELPER: Calculate rides with hybrid approach
# ============================================================================

def calculate_realistic_rides(
    ml_prediction: float,
    distance_km: float,
    duration_min: float,
    driver_shift_hours: float,
    driver_rating: float,
    rides_completed_so_far: float
) -> dict:
    """
    Calculate rides prediction with weighted blend (not just max).
    
    Args:
        ml_prediction: ML model's rides prediction
        distance_km: Trip distance
        duration_min: Trip duration (avg for this trip)
        driver_shift_hours: Shift duration so far
        driver_rating: Driver rating (affects efficiency)
        rides_completed_so_far: Rides so far
    
    Returns:
        dict with predicted_rides and breakdown
    """
    
    # ML prediction (already accounts for patterns)
    ml_rides = max(1, int(round(ml_prediction)))
    
    # Time-based rule
    # Avg ride duration varies: 15-30 min typical
    # 12-hour shift constraint = max 48 rides
    # But driver might be able to do 50-60 with efficiency
    
    # Adjust duration based on driver rating (high rated = faster turnaround)
    efficiency_factor = 0.9 + (driver_rating - 3.5) * 0.05  # 0.9x to 1.25x
    adjusted_duration = duration_min / efficiency_factor
    
    # Remaining shift time
    remaining_hours = max(0, (12 - driver_shift_hours))  # Assume 12-hour shifts
    remaining_minutes = remaining_hours * 60
    
    # Time-based estimate
    time_based_rides = max(1, int(remaining_minutes / (adjusted_duration + 5)))  # 5 min buffer
    
    # Weighted blend (not just max!)
    # Weight towards ML for experienced drivers
    experience_factor = min(1.0, rides_completed_so_far / 1000)  # Increase weight with experience
    
    ml_weight = 0.4 + (experience_factor * 0.2)  # 40-60% ML weight
    time_weight = 1 - ml_weight
    
    predicted_rides = int(round(
        ml_weight * ml_rides +
        time_weight * time_based_rides
    ))
    
    # Sanity bounds
    predicted_rides = np.clip(predicted_rides, 1, 60)
    
    return {
        "predicted_rides": predicted_rides,
        "ml_estimate": ml_rides,
        "time_estimate": time_based_rides,
        "ml_weight": round(ml_weight, 2),
        "efficiency_factor": round(efficiency_factor, 2)
    }


# ============================================================================
# MAIN PREDICTION ENDPOINT (IMPROVED)
# ============================================================================

@router.post("/predict")
def predict(data: PredictionRequest):
    """
    Improved predict endpoint with realistic revenue and rides estimation.
    """
    
    try:
        logger.info("🚀 Prediction request received")
        input_data = data.dict()
        
        # ========== STEP 1: GET DISTANCE & DURATION ==========
        try:
            maps = get_distance_duration(
                data.pickup_lat,
                data.pickup_lng,
                data.drop_lat,
                data.drop_lng
            )
            logger.info(f"Maps: {maps['distance_km']:.2f}km, {maps['duration_min']:.1f}min")
        except Exception as e:
            logger.error(f"Maps API failed: {e}")
            raise HTTPException(status_code=500, detail="Maps service unavailable")
        
        # ========== STEP 2: BUILD FEATURES ==========
        try:
            X_scaled, feature_dict, feature_warnings = build_inference_features(
                input_data,
                maps
            )
            
            if feature_warnings:
                logger.warning(f"Feature warnings: {feature_warnings}")
        
        except Exception as e:
            logger.error(f"Feature engineering failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid features: {str(e)}")
        
        # ========== STEP 3: GET ML PREDICTIONS ==========
        try:
            # Revenue prediction (log scale from model)
            log_revenue_pred = get_model_predictions(X_scaled, revenue_model)
            ml_revenue_pred = float(np.expm1(log_revenue_pred))  # Inverse log
            ml_revenue_pred = max(25, ml_revenue_pred)  # Ensure minimum
            
            logger.info(f"ML Revenue: ₹{ml_revenue_pred:.2f}")
            
            # Rides prediction
            ml_rides_pred = get_model_predictions(X_scaled, rides_model)
            logger.info(f"ML Rides: {ml_rides_pred:.1f}")
        
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            raise HTTPException(status_code=500, detail="Model inference failed")
        
        # ========== STEP 4: CALCULATE BUSINESS LOGIC REVENUE ==========
        try:
            # Extract flags from input
            hour = data.hour_of_day
            day = data.day_of_week if hasattr(data, 'day_of_week') else 0
            
            is_morning_peak = 6 <= hour <= 9
            is_evening_peak = 17 <= hour <= 20
            is_late_night = hour >= 22 or hour <= 1
            is_weekend_noon = (day >= 5) and (12 <= hour <= 14)
            is_night = hour >= 22 or hour <= 6
            
            # Use improved pricing function
            pricing_result = calculate_realistic_revenue(
                distance_km=maps["distance_km"],
                duration_min=maps["duration_min"],
                surge_multiplier=data.surge_multiplier,
                zone_surge_multiplier=data.zone_surge_multiplier,
                is_morning_peak=is_morning_peak,
                is_evening_peak=is_evening_peak,
                is_night=is_night,
                is_late_night=is_late_night,
                is_weekend_noon=is_weekend_noon,
                is_raining=data.is_raining,
                weather_type=data.weather_type if hasattr(data, 'weather_type') else "clear",
                waiting_time_min=data.waiting_time_min,
                total_km_today=data.total_op_km_today,
                driver_rating=data.driver_rating,
                is_female_driver=data.is_female_driver if hasattr(data, 'is_female_driver') else False,
                ml_prediction=ml_revenue_pred,
                ml_weight=ML_WEIGHT_REVENUE
            )
            
            final_revenue = pricing_result["final_revenue"]
            logger.info(f"Final Revenue: ₹{final_revenue:.2f} (ML weight: {ML_WEIGHT_REVENUE})")
        
        except Exception as e:
            logger.error(f"Pricing calculation failed: {e}")
            raise HTTPException(status_code=500, detail="Revenue calculation failed")
        
        # ========== STEP 5: CALCULATE RIDES ==========
        try:
            rides_breakdown = calculate_realistic_rides(
                ml_prediction=ml_rides_pred,
                distance_km=maps["distance_km"],
                duration_min=maps["duration_min"],
                driver_shift_hours=data.driver_shift_hours_elapsed,
                driver_rating=data.driver_rating,
                rides_completed_so_far=data.rides_completed_so_far if hasattr(data, 'rides_completed_so_far') else 5
            )
            
            predicted_rides = rides_breakdown["predicted_rides"]
            logger.info(f"Predicted Rides: {predicted_rides}")
        
        except Exception as e:
            logger.error(f"Rides calculation failed: {e}")
            predicted_rides = max(1, int(np.expm1(log_revenue_pred) / 50))  # Fallback
        
        # ========== STEP 6: CALCULATE CONFIDENCE ==========
        try:
            confidence = calculate_confidence_score(
                predicted_revenue=final_revenue,
                base_business_revenue=pricing_result["after_multipliers"],
                ml_predicted_revenue=ml_revenue_pred,
                distance_km=maps["distance_km"],
                model_r2=0.75  # TODO: Load from saved metrics
            )
            logger.info(f"Confidence: {confidence}")
        
        except Exception as e:
            confidence = 0.65  # Safe default
            logger.warning(f"Confidence calculation failed: {e}")
        
        # ========== STEP 7: SANITY CHECKS ==========
        is_reasonable, sanity_warnings = sanity_check_prediction(
            final_revenue,
            input_data,
            feature_dict
        )
        
        # ========== STEP 8: EXPLAINABILITY ==========
        try:
            explanation = get_shap_explanation(X_scaled, top_k=5)
        except Exception as e:
            logger.warning(f"SHAP failed: {e}")
            explanation = []
        
        # ========== STEP 9: DRIFT DETECTION ==========
        try:
            drift = check_drift(feature_dict)
            drift_detected = any(v.get("drift", False) for v in drift.values())
        except Exception as e:
            logger.warning(f"Drift detection failed: {e}")
            drift = {}
            drift_detected = False
        
        # ========== STEP 10: BUILD RESPONSE ==========
        
        # Revenue ranges
        revenue_range = (
            round(final_revenue * 0.85, 2),
            round(final_revenue * 1.15, 2)
        )
        
        # Rides ranges
        rides_range = (
            max(1, predicted_rides - 2),
            predicted_rides + 2
        )
        
        output = {
            "prediction_status": "success",
            "predicted_revenue": round(final_revenue, 2),
            "predicted_rides": predicted_rides,
            "earnings_range": f"₹{revenue_range[0]} - ₹{revenue_range[1]}",
            "rides_range": f"{rides_range[0]} - {rides_range[1]} rides",
            "confidence": confidence,
            "confidence_breakdown": {
                "model_quality": "Good (R² ~0.75)",
                "prediction_stability": f"{'High' if ML_WEIGHT_REVENUE < 0.35 else 'Medium'}",
                "distance_km": maps["distance_km"]
            },
            "revenue_breakdown": {
                "base_fare": pricing_result["base_fare"],
                "after_surge_and_multipliers": pricing_result["after_multipliers"],
                "ml_contribution": f"₹{pricing_result['ml_prediction']} ({int(ML_WEIGHT_REVENUE*100)}%)" if pricing_result.get("ml_prediction") else "N/A",
                "bonus_amount": pricing_result["bonus_amount"]
            },
            "rides_breakdown": {
                "ml_estimate": rides_breakdown["ml_estimate"],
                "time_estimate": rides_breakdown["time_estimate"],
                "efficiency_factor": rides_breakdown["efficiency_factor"]
            },
            "explainability": explanation,
            "alerts": []
        }
        
        # Add warnings/drift
        if sanity_warnings:
            output["sanity_warnings"] = sanity_warnings
        
        if drift_detected:
            output["drift_alert"] = "⚠️  Unusual input detected (data drift)"
        
        # ========== STEP 11: MONITORING & ALERTS ==========
        try:
            log_prediction(input_data, output)
            
            alerts = check_alerts(output)
            if alerts:
                output["alerts"] = alerts
        
        except Exception as e:
            logger.warning(f"Monitoring failed: {e}")
        
        logger.info("✅ Prediction completed successfully")
        return output
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        return {
            "prediction_status": "error",
            "message": f"Prediction failed: {str(e)}",
            "error_type": type(e).__name__
        }


# ============================================================================
# HEALTH CHECK & DEBUG ENDPOINTS
# ============================================================================

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ml_weight_revenue": ML_WEIGHT_REVENUE,
        "ml_weight_rides": ML_WEIGHT_RIDES,
        "pricing_model": "Realistic Uber/Ola style"
    }
