"""
CENTRALIZED FEATURE ENGINEERING LOGIC

This file is the single source of truth for all feature engineering.
Use this in training AND inference to prevent data drift.

Features are organized by category:
1. Temporal features (time of day, day of week)
2. Location features (demand, supply, surge)
3. Driver features (rating, experience, efficiency)
4. Trip features (distance, duration, waiting)
5. Environmental features (weather, special events)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple


# ============================================================================
# FEATURE NAMES (Single Source of Truth)
# ============================================================================

TEMPORAL_FEATURES = [
    "hour_of_day",
    "day_of_week",
    "is_peak_hour",
    "is_morning_peak",
    "is_evening_peak",
    "is_night_trip",
    "is_weekend"
]

LOCATION_FEATURES = [
    "demand_supply_ratio",
    "zone_surge_multiplier",
    "demand_intensity",
    "supply_level"
]

DRIVER_FEATURES = [
    "driver_rating",
    "driver_total_trips",
    "driver_experience_level",
    "driver_shift_hours_elapsed",
    "rides_completed_so_far"
]

TRIP_FEATURES = [
    "trip_distance",
    "trip_duration_min",
    "avg_speed",
    "waiting_time_min",
    "total_op_km_today"
]

ENVIRONMENT_FEATURES = [
    "surge_multiplier",
    "is_raining",
    "weather_type",
    "is_holiday"
]

ALL_FEATURES = (
    TEMPORAL_FEATURES +
    LOCATION_FEATURES +
    DRIVER_FEATURES +
    TRIP_FEATURES +
    ENVIRONMENT_FEATURES
)

print(f"✅ Total Features: {len(ALL_FEATURES)}")


# ============================================================================
# FEATURE ENGINEERING FUNCTIONS
# ============================================================================

def engineer_temporal_features(input_data: Dict) -> Dict:
    """Extract and engineer temporal features from hour and day info."""
    
    hour = input_data.get("hour_of_day", 12)
    day_of_week = input_data.get("day_of_week", 0)  # 0=Monday, 6=Sunday
    
    # Basic temporal
    features = {
        "hour_of_day": float(hour),
        "day_of_week": float(day_of_week),
        "is_weekend": float(day_of_week >= 5),  # Saturday/Sunday
    }
    
    # Peak hours (Expanded & realistic for Indian cities)
    # Morning: 6-9am, Evening: 5-8pm, Late night: 10pm-midnight, Weekend noon peak: 12-2pm
    morning_peak = 6 <= hour <= 9
    evening_peak = 17 <= hour <= 20
    late_night = hour >= 22 or hour <= 1
    weekend_noon = (day_of_week >= 5) and (12 <= hour <= 14)
    
    features["is_peak_hour"] = float(morning_peak or evening_peak or late_night or weekend_noon)
    features["is_morning_peak"] = float(morning_peak)
    features["is_evening_peak"] = float(evening_peak)
    
    # Night (10pm - 6am)
    features["is_night_trip"] = float(hour >= 22 or hour <= 6)
    
    return features


def engineer_location_features(input_data: Dict) -> Dict:
    """Engineer demand/supply and surge-related features."""
    
    rides_zone = float(input_data.get("number_of_rides_in_zone", 50))
    drivers_zone = float(input_data.get("number_of_active_drivers_in_zone", 20))
    zone_surge = float(input_data.get("zone_surge_multiplier", 1.0))
    
    # Demand-supply ratio (log-normalized for stability)
    demand_supply_ratio = np.log1p(rides_zone / (drivers_zone + 1e-6))
    
    # Supply level (categorized)
    supply_level = np.log1p(drivers_zone)
    
    # Demand intensity (combines rides + surge)
    demand_intensity = rides_zone * zone_surge
    
    return {
        "demand_supply_ratio": float(demand_supply_ratio),
        "zone_surge_multiplier": float(zone_surge),
        "demand_intensity": float(demand_intensity),
        "supply_level": float(supply_level)
    }


def engineer_driver_features(input_data: Dict) -> Dict:
    """Engineer driver-specific features."""
    
    rating = float(input_data.get("driver_rating", 4.5))
    total_trips = float(input_data.get("driver_total_trips", 1000))
    shift_hours = float(input_data.get("driver_shift_hours_elapsed", 6))
    rides_completed = float(input_data.get("rides_completed_so_far", 5))
    
    # Experience level (categorical -> numeric)
    # Total trips: 0-500=new, 500-2000=intermediate, 2000-5000=experienced, 5000+=veteran
    if total_trips < 500:
        exp_level = 1.0  # New
    elif total_trips < 2000:
        exp_level = 2.0  # Intermediate
    elif total_trips < 5000:
        exp_level = 3.0  # Experienced
    else:
        exp_level = 4.0  # Veteran
    
    # Rides per hour (efficiency metric)
    rides_per_hour = rides_completed / (shift_hours + 1e-6)
    
    return {
        "driver_rating": float(rating),
        "driver_total_trips": float(np.log1p(total_trips)),  # Log normalize
        "driver_experience_level": float(exp_level),
        "driver_shift_hours_elapsed": float(shift_hours),
        "rides_completed_so_far": float(rides_completed)
    }


def engineer_trip_features(input_data: Dict, maps_data: Dict = None) -> Dict:
    """Engineer trip-specific features."""
    
    if maps_data:
        distance = float(maps_data.get("distance_km", 5))
        duration = float(maps_data.get("duration_min", 15))
    else:
        distance = float(input_data.get("distance_km", 5))
        duration = float(input_data.get("duration_min", 15))
    
    waiting_time = float(input_data.get("waiting_time_min", 0))
    total_km_today = float(input_data.get("total_op_km_today", 80))
    
    # Average speed (km/min)
    avg_speed = distance / (duration + 1e-6)
    
    return {
        "trip_distance": float(distance),
        "trip_duration_min": float(duration),
        "avg_speed": float(avg_speed),
        "waiting_time_min": float(waiting_time),
        "total_op_km_today": float(total_op_km_today)
    }


def engineer_environment_features(input_data: Dict) -> Dict:
    """Engineer environmental/external features."""
    
    surge = float(input_data.get("surge_multiplier", 1.0))
    is_raining = float(input_data.get("is_raining", False))
    is_holiday = float(input_data.get("is_holiday", False))
    
    # Weather type (categorical)
    weather_type_str = input_data.get("weather_type", "clear")
    weather_mapping = {
        "clear": 0.0,
        "cloudy": 1.0,
        "rainy": 2.0,
        "heavy_rain": 3.0,
        "fog": 4.0
    }
    weather_type = float(weather_mapping.get(weather_type_str.lower(), 0.0))
    
    return {
        "surge_multiplier": float(surge),
        "is_raining": float(is_raining),
        "weather_type": float(weather_type),
        "is_holiday": float(is_holiday)
    }


# ============================================================================
# MAIN FEATURE BUILDER (USE THIS EVERYWHERE!)
# ============================================================================

def build_feature_vector(input_data: Dict, maps_data: Dict = None) -> Tuple[Dict, list]:
    """
    Build complete feature vector from input data.
    
    Returns:
        Tuple of:
        - feature_dict: Dict with all engineered features
        - feature_list: List in exact order matching ALL_FEATURES
    
    IMPORTANT: This is used in both training and inference!
    """
    
    # Engineer all features
    temporal = engineer_temporal_features(input_data)
    location = engineer_location_features(input_data)
    driver = engineer_driver_features(input_data)
    trip = engineer_trip_features(input_data, maps_data)
    environment = engineer_environment_features(input_data)
    
    # Combine into single dict
    feature_dict = {
        **temporal,
        **location,
        **driver,
        **trip,
        **environment
    }
    
    # Create ordered list matching ALL_FEATURES
    feature_list = [feature_dict.get(feat, 0.0) for feat in ALL_FEATURES]
    
    # Validate
    assert len(feature_list) == len(ALL_FEATURES), f"Feature count mismatch: {len(feature_list)} vs {len(ALL_FEATURES)}"
    
    return feature_dict, feature_list


# ============================================================================
# BOUNDS & VALIDATION (Production Safety)
# ============================================================================

FEATURE_BOUNDS = {
    "hour_of_day": (0, 23),
    "day_of_week": (0, 6),
    "trip_distance": (0.5, 100),
    "trip_duration_min": (1, 180),
    "driver_rating": (1, 5),
    "avg_speed": (0.1, 50),
    "demand_supply_ratio": (-2, 8),  # After log transform
    "surge_multiplier": (0.5, 5),
    "zone_surge_multiplier": (0.5, 5)
}


def validate_features(feature_dict: Dict) -> Tuple[bool, list]:
    """
    Validate features are within expected bounds.
    Returns: (is_valid, list_of_warnings)
    """
    warnings = []
    
    for feature, (min_val, max_val) in FEATURE_BOUNDS.items():
        if feature not in feature_dict:
            continue
        
        value = feature_dict[feature]
        
        if value < min_val or value > max_val:
            warnings.append(
                f"⚠️  {feature}={value:.2f} outside bounds [{min_val}, {max_val}]"
            )
    
    return len(warnings) == 0, warnings


if __name__ == "__main__":
    # Test feature engineering
    test_input = {
        "hour_of_day": 18,
        "day_of_week": 4,  # Friday
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
        "weather_type": "clear"
    }
    
    feature_dict, feature_list = build_feature_vector(test_input)
    print("✅ Feature Engineering Test Passed")
    print(f"Features: {len(feature_list)}")
    print(f"Sample features: {list(feature_dict.items())[:5]}")
