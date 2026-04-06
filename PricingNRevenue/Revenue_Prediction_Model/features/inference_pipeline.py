"""
IMPROVED FEATURE PIPELINE FOR INFERENCE

Uses centralized feature engineering from feature_definitions.py
Ensures consistency between training and inference!
"""

import joblib
import numpy as np
import os
from utils.logger import get_logger
from features.feature_definitions import (
    build_feature_vector,
    validate_features,
    ALL_FEATURES
)

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")

# Load artifacts
scaler = joblib.load(SCALER_PATH)
feature_columns = joblib.load(COLUMNS_PATH)


def build_inference_features(input_data: dict, maps_data: dict = None):
    """
    Build feature vector for inference.
    
    Args:
        input_data: Input parameters from API request
        maps_data: Augmented data from Google Maps (distance, duration)
    
    Returns:
        Tuple of:
        - X_scaled: Numpy array (1, 32) ready for model prediction
        - feature_dict: Dictionary with all engineered features
        - validation_warnings: List of any warnings
    """
    
    try:
        # Merge maps data into input
        if maps_data:
            input_data_merged = {**input_data, **maps_data}
        else:
            input_data_merged = input_data.copy()
        
        # Build feature vector using centralized function
        feature_dict, feature_list = build_feature_vector(input_data_merged)
        
        # Validate features
        is_valid, warnings = validate_features(feature_dict)
        
        if warnings:
            for warning in warnings:
                logger.warning(warning)
        
        # Convert to numpy array
        X = np.array(feature_list).reshape(1, -1)
        
        # Scale using saved scaler
        X_scaled = scaler.transform(X)
        
        logger.info(f"✅ Feature pipeline: {X_scaled.shape}")
        
        return X_scaled, feature_dict, warnings
    
    except Exception as e:
        logger.error(f"❌ Feature pipeline failed: {str(e)}", exc_info=True)
        raise


def get_model_predictions(X_scaled, model):
    """Get raw predictions from model."""
    try:
        prediction = float(model.predict(X_scaled)[0])
        return prediction
    except Exception as e:
        logger.error(f"❌ Model prediction failed: {str(e)}")
        raise


# ============================================================================
# PREDICTION CONFIDENCE & UNCERTAINTY (For better confidence scores)
# ============================================================================

def get_prediction_uncertainty(model, X_scaled, X_train_scaled=None):
    """
    Calculate prediction uncertainty/variance.
    
    For tree-based models: uses variance across leaves
    For linear models: uses residuals from training data
    """
    
    try:
        # For XGBoost/RandomForest: predict with raw leaf values
        if hasattr(model, "predict_proba"):
            # Regression doesn't use proba, but we can get variance
            pass
        
        # Simple approach: use prediction std from training data
        # This requires storing training data stats
        # For now, return None and use confidence formula without it
        
        return None
    
    except:
        return None


def sanity_check_prediction(predicted_value, input_data, feature_dict):
    """
    Sanity checks on prediction.
    Returns: (is_reasonable, warnings)
    """
    
    warnings = []
    
    # Check 1: Revenue sanity
    if predicted_value < 25:
        warnings.append(f"⚠️  Very low revenue: {predicted_value:.2f} INR")
    
    if predicted_value > 1000:
        warnings.append(f"⚠️  Very high revenue: {predicted_value:.2f} INR")
    
    # Check 2: Surge sanity
    surge = input_data.get("surge_multiplier", 1.0)
    base_expected = 100 * surge  # Rough estimate
    if predicted_value > base_expected * 2:
        warnings.append(f"⚠️  Revenue {predicted_value:.2f} exceeds expected {base_expected*2:.2f} with surge={surge}")
    
    # Check 3: Check if features are reasonable
    distance = input_data.get("distance_km", 5)
    duration = input_data.get("duration_min", 15)
    
    if distance < 0.5 or distance > 100:
        warnings.append(f"⚠️  Unusual distance: {distance} km")
    
    if duration < 1 or duration > 360:
        warnings.append(f"⚠️  Unusual duration: {duration} min")
    
    is_reasonable = len(warnings) == 0
    
    return is_reasonable, warnings


if __name__ == "__main__":
    # Test feature pipeline
    test_input = {
        "hour_of_day": 18,
        "day_of_week": 4,
        "distance_km": 10,
        "duration_min": 25,
        "driver_rating": 4.7,
        "driver_total_trips": 3000,
        "driver_shift_hours_elapsed": 5,
        "rides_completed_so_far": 12,
        "number_of_rides_in_zone": 80,
        "number_of_active_drivers_in_zone": 30,
        "zone_surge_multiplier": 1.5,
        "surge_multiplier": 1.5,
        "total_op_km_today": 90,
        "waiting_time_min": 2,
        "is_raining": False,
        "weather_type": "clear",
        "is_holiday": False
    }
    
    X_scaled, feature_dict, warnings = build_inference_features(test_input)
    print("✅ Feature pipeline test passed")
    print(f"Shape: {X_scaled.shape}")
    print(f"Warnings: {warnings}")
