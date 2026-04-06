"""
IMPROVED PREPROCESSING - Production Ready

Key Improvements:
1. Creates rides_per_hour target (not cumulative rides)
2. Better feature engineering
3. Handles NaN values properly
4. Creates all necessary features for both training and inference
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config.settings import MODEL_DIR


# ============================================================================
# FEATURE ENGINEERING FUNCTIONS
# ============================================================================

def engineer_temporal_features(df):
    """Create time-based features."""
    df["is_peak_hour"] = df["hour_of_day"].isin([8, 9, 18, 19, 20]).astype(int)
    df["is_night_trip"] = ((df["hour_of_day"] >= 22) | (df["hour_of_day"] <= 5)).astype(int)
    
    # Better peak detection (comprehensive)
    df["is_morning_peak"] = df["hour_of_day"].isin([6, 7, 8, 9]).astype(int)
    df["is_lunch_rush"] = df["hour_of_day"].isin([12, 13]).astype(int)
    df["is_evening_peak"] = df["hour_of_day"].isin([17, 18, 19, 20]).astype(int)
    df["is_late_night"] = df["hour_of_day"].isin([22, 23, 0, 1, 2]).astype(int)
    
    return df


def engineer_supply_demand_features(df):
    """Create supply-demand features."""
    # Demand-Supply Ratio (critical for surge prediction)
    df["demand_supply_ratio"] = (
        df["number_of_rides_in_zone"] /
        (df["number_of_active_drivers_in_zone"] + 1)
    )
    
    # Supply level indicator
    df["low_supply"] = (df["number_of_active_drivers_in_zone"] < 20).astype(int)
    df["high_demand"] = (df["number_of_rides_in_zone"] > 50).astype(int)
    
    # Demand intensity (rides * surge)
    df["demand_intensity"] = (
        df["number_of_rides_in_zone"] * 
        (df.get("zone_surge_multiplier", 1.0) + 1)  # Handle missing surge
    )
    
    return df


def engineer_trip_features(df):
    """Create trip-based features."""
    # Avoid division by zero
    df["trip_duration_min"] = df["trip_duration_min"].clip(lower=1)
    df["trip_distance"] = df["trip_distance"].clip(lower=0.1)
    df["driver_shift_hours_elapsed"] = df.get("driver_shift_hours_elapsed", 1).clip(lower=1)
    
    # Average speed (km/h)
    df["avg_speed"] = (df["trip_distance"] / df["trip_duration_min"]) * 60
    df["avg_speed"] = df["avg_speed"].clip(0, 120)  # Sanity check
    
    # Ride efficiency
    df["ride_efficiency"] = df["trip_distance"] / (df["trip_duration_min"] + 1)
    
    # Trip classification
    df["is_short_trip"] = (df["trip_distance"] < 2).astype(int)
    df["is_long_trip"] = (df["trip_distance"] > 15).astype(int)
    
    return df


def engineer_driver_features(df):
    """Create driver-based features."""
    # Driver experience level
    df["is_new_driver"] = (df["driver_total_trips"] < 100).astype(int)
    df["is_experienced_driver"] = (df["driver_total_trips"] > 1000).astype(int)
    
    # Driver rating interaction with surge
    df["high_rated_driver"] = (df["driver_rating"] >= 4.5).astype(int)
    df["low_rated_driver"] = (df["driver_rating"] < 3.5).astype(int)
    
    # Shift progress
    df["shift_progress_percent"] = (df["driver_shift_hours_elapsed"] / 12) * 100
    df["shift_progress_percent"] = df["shift_progress_percent"].clip(0, 100)
    
    return df


def create_rides_per_hour(df):
    """
    CRITICAL FIX: Create rides_per_hour target
    
    This is the KEY FIX for unrealistic rides predictions.
    Instead of training on cumulative rides (which can be 100+),
    we train on rides per hour (typically 2-4 per hour).
    """
    # Ensure no division by zero
    df["driver_shift_hours_elapsed"] = df.get("driver_shift_hours_elapsed", 1).clip(lower=1)
    
    # Create rides_per_hour
    df["rides_per_hour"] = (
        df["rides_completed_so_far"] / 
        (df["driver_shift_hours_elapsed"] + 1)
    ).clip(lower=0.1, upper=4.0)  # Realistic range: 0.1-4 rides/hour
    
    # Also keep cumulative for reference
    df["rides_cumulative"] = df["rides_completed_so_far"].clip(lower=1)
    
    return df


def engineer_bonus_features(df):
    """Create bonus/incentive features."""
    df["extra_km"] = (df["total_op_km_today"] - 135).clip(lower=0)
    df["extra_bonus"] = df["extra_km"] * 12
    df["km_milestone_100"] = (df["total_op_km_today"] >= 100).astype(int)
    df["km_milestone_150"] = (df["total_op_km_today"] >= 150).astype(int)
    df["km_milestone_200"] = (df["total_op_km_today"] >= 200).astype(int)
    
    return df


def engineer_weather_features(df):
    """Create weather-based features."""
    # If weather data exists
    if "is_raining" in df.columns:
        df["weather_surge_multiplier"] = (1 + 0.1 * df["is_raining"].astype(int))
    else:
        df["weather_surge_multiplier"] = 1.0
    
    return df


# ============================================================================
# MAIN PREPROCESSING
# ============================================================================

def preprocess_data(df):
    """
    Main preprocessing pipeline.
    
    Output:
    - Cleaned and engineered data
    - rides_per_hour target for training
    - All features scaled and ready
    """
    
    print("🧹 Starting preprocessing pipeline...")
    
    # ===== VALIDATION =====
    required_cols = [
        "hour_of_day",
        "trip_distance",
        "trip_duration_min",
        "fare_amount",
        "rides_completed_so_far",
        "driver_shift_hours_elapsed",
        "number_of_rides_in_zone",
        "number_of_active_drivers_in_zone",
        "driver_rating",
        "driver_total_trips",
        "total_op_km_today",
        "surge_multiplier"
    ]
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"❌ Missing column: {col}")
    
    print(f"✅ All required columns present")
    
    # ===== CLEANING =====
    print("🧹 Cleaning data...")
    
    # Remove duplicates
    df = df.drop_duplicates()
    print(f"   Duplicates removed: {len(df)} rows remaining")
    
    # Handle NaN
    df = df.fillna(df.median(numeric_only=True))
    print(f"   NaN values filled")
    
    # Remove outliers (extreme values)
    df = df[df["fare_amount"] > 0]
    df = df[df["trip_distance"] > 0]
    df = df[df["trip_duration_min"] > 0]
    df = df[df["driver_rating"] > 0]
    print(f"   Outliers removed: {len(df)} rows remaining")
    
    # ===== FEATURE ENGINEERING =====
    print("🔧 Engineering features...")
    
    df = engineer_temporal_features(df)
    df = engineer_supply_demand_features(df)
    df = engineer_trip_features(df)
    df = engineer_driver_features(df)
    df = engineer_bonus_features(df)
    df = engineer_weather_features(df)
    
    # 🚀 CRITICAL: Create rides_per_hour
    df = create_rides_per_hour(df)
    print(f"   ✅ Created rides_per_hour (mean: {df['rides_per_hour'].mean():.2f}, max: {df['rides_per_hour'].max():.2f})")
    
    # ===== SAVE PROCESSED DATA =====
    print("💾 Saving processed data...")
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/processed_data.csv", index=False)
    print(f"   Saved to data/processed/processed_data.csv")
    
    # ===== PREPARE FEATURES =====
    print("📊 Preparing feature set...")
    
    FEATURE_COLUMNS = [
        # Temporal
        "hour_of_day",
        "is_peak_hour",
        "is_night_trip",
        "is_morning_peak",
        "is_lunch_rush",
        "is_evening_peak",
        "is_late_night",
        
        # Trip
        "trip_distance",
        "trip_duration_min",
        "avg_speed",
        "ride_efficiency",
        "is_short_trip",
        "is_long_trip",
        
        # Driver
        "driver_rating",
        "driver_total_trips",
        "driver_shift_hours_elapsed",
        "is_new_driver",
        "is_experienced_driver",
        "high_rated_driver",
        "low_rated_driver",
        "shift_progress_percent",
        
        # Supply-Demand
        "number_of_rides_in_zone",
        "number_of_active_drivers_in_zone",
        "demand_supply_ratio",
        "low_supply",
        "high_demand",
        "demand_intensity",
        
        # Surge & Pricing
        "surge_multiplier",
        "zone_surge_multiplier",
        "weather_surge_multiplier",
        
        # Logistics
        "total_op_km_today",
        "extra_km",
        "km_milestone_100",
        "km_milestone_150",
        "km_milestone_200",
        "extra_bonus",
        
        # NEW KEY FEATURE
        "rides_per_hour"  # KEY: For training rides model
    ]
    
    # Validate all features exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"❌ Feature missing: {col}")
    
    X = df[FEATURE_COLUMNS]
    print(f"✅ Feature set ready: {len(FEATURE_COLUMNS)} features")
    
    # ===== TARGETS =====
    print("🎯 Preparing targets...")
    
    # Revenue target
    y_revenue = df["fare_amount"].clip(lower=25, upper=5000)
    
    # Rides target (rides_per_hour, not cumulative!)
    y_rides_per_hour = df["rides_per_hour"]
    
    print(f"   Revenue target - Mean: ₹{y_revenue.mean():.2f}, Std: ₹{y_revenue.std():.2f}")
    print(f"   Rides/hour target - Mean: {y_rides_per_hour.mean():.2f}, Std: {y_rides_per_hour.std():.2f}")
    print(f"   Rides/hour range: {y_rides_per_hour.min():.2f} - {y_rides_per_hour.max():.2f}")
    
    # ===== SCALING =====
    print("📈 Scaling features...")
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
    joblib.dump(FEATURE_COLUMNS, f"{MODEL_DIR}/columns.pkl")
    print(f"   Scaler saved to {MODEL_DIR}/scaler.pkl")
    
    print("✅ Preprocessing complete!")
    print("\n" + "="*70)
    print(f"Dataset shape: {X.shape}")
    print(f"Features: {len(FEATURE_COLUMNS)}")
    print(f"Revenue range: ₹{y_revenue.min():.2f} - ₹{y_revenue.max():.2f}")
    print(f"Rides/hour range: {y_rides_per_hour.min():.2f} - {y_rides_per_hour.max():.2f}")
    print("="*70)
    
    return X_scaled, y_revenue, y_rides_per_hour, FEATURE_COLUMNS, df


if __name__ == "__main__":
    # Example usage
    df = pd.read_csv("data/raw/your_data.csv")  # Replace with actual data path
    X_scaled, y_revenue, y_rides_per_hour, features, processed_df = preprocess_data(df)
    print("\n✅ Preprocessing complete! Ready for training.")

