"""
IMPROVED BUSINESS LOGIC FOR PRICING

Real-world ride-hailing revenue model based on Uber/Ola pricing:
1. Base fare (minimum charge)
2. Distance charge (per km)
3. Time charge (per minute waiting)
4. Surge multiplier (supply-demand)
5. Peak hour multiplier (time-based)
6. Night multiplier (safety premium)
7. Weather multiplier (rain/special conditions)
8. Destination multiplier (high-demand areas)
9. Driver incentive/bonus (completion bonus)

This replaces the overly simple pricing_service.py logic.
"""

import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# PRICING CONSTANTS (Tuned for Indian ride-hailing market)
# ============================================================================

BASE_FARE = 50  # Minimum charge in INR

# Distance rates (per km after first 1.5 km)
DISTANCE_RATE = 25  # INR/km

# Time charge (per minute)
TIME_RATE = 2  # INR/minute (applicable after 5 min cutoff)
TIME_CUTOFF_MIN = 5  # First 5 minutes included in base

# Surge multiplier ranges (based on real Uber pricing)
SURGE_LEVELS = {
    "low": 1.0,      # < 0.5
    "normal": 1.2,   # 0.5 - 1.0
    "moderate": 1.5, # 1.0 - 1.5
    "high": 2.0,     # 1.5 - 2.5
    "critical": 2.5  # > 2.5
}

# Peak hour multipliers (stacked on top of surge)
PEAK_MULTIPLIERS = {
    "morning_peak": 1.25,   # 6-9am rush
    "evening_peak": 1.35,   # 5-8pm heavy rush
    "late_night": 1.5,      # 10pm-1am (safety premium)
    "weekend_noon": 1.2,    # 12-2pm weekend
    "normal": 1.0
}

# Night multiplier
NIGHT_MULTIPLIER = 1.6  # 10pm-6am safety surcharge

# Weather conditions
WEATHER_MULTIPLIERS = {
    "clear": 1.0,
    "cloudy": 1.0,
    "light_rain": 1.15,
    "heavy_rain": 1.35,
    "fog": 1.2
}

# Location/zone multipliers
ZONE_SURGE_MAX = 2.5  # Cap zone surge
ZONE_SURGE_MIN = 0.8  # Floor zone surge

# Bonus structure
DAILY_KM_TARGET = 135  # Incentive threshold
BONUS_RATE_PER_KM = 12  # INR per km after target

# Female driver bonus (inclusive ride-hailing)
FEMALE_DRIVER_BONUS = 1.05  # 5% bonus

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_surge_level(surge_multiplier):
    """Categorize surge level."""
    if surge_multiplier < 0.5:
        return "low"
    elif surge_multiplier < 1.0:
        return "normal"
    elif surge_multiplier < 1.5:
        return "moderate"
    elif surge_multiplier < 2.5:
        return "high"
    else:
        return "critical"


def get_peak_multiplier(is_morning_peak, is_evening_peak, is_late_night, is_weekend_noon):
    """Get peak hour multiplier (choose highest applicable)."""
    
    multipliers = []
    
    if is_morning_peak:
        multipliers.append(PEAK_MULTIPLIERS["morning_peak"])
    if is_evening_peak:
        multipliers.append(PEAK_MULTIPLIERS["evening_peak"])
    if is_late_night:
        multipliers.append(PEAK_MULTIPLIERS["late_night"])
    if is_weekend_noon:
        multipliers.append(PEAK_MULTIPLIERS["weekend_noon"])
    
    # Use highest peak multiplier (don't stack, they overlap)
    return max(multipliers) if multipliers else PEAK_MULTIPLIERS["normal"]


def apply_surge_saturation(surge_multiplier):
    """
    Surge saturation curve.
    Real-world: 2x surge isn't exactly 2x price due to reduced demand.
    Uses: price_multiplier = 1 + 0.8 * (surge - 1)
    """
    if surge_multiplier <= 1.0:
        return 1.0
    
    # Saturating curve (diminishing returns)
    saturation = 1.0 + 0.8 * np.log1p(surge_multiplier - 1)
    
    return min(saturation, SURGE_LEVELS["critical"])


def calculate_distance_charge(distance_km, is_night=False):
    """Calculate distance component."""
    
    # First 1.5km included in base (reduced)
    extra_distance = max(0, distance_km - 1.5)
    
    distance_charge = extra_distance * DISTANCE_RATE
    
    # Night distance premium (more charges for safety)
    if is_night:
        distance_charge *= 1.1
    
    return distance_charge


def calculate_time_charge(duration_min, waiting_time_min=0):
    """Calculate time component."""
    
    # Moving time charge (high duration = inefficiency)
    # Only charge for time > 5 minutes
    moving_time_charge = max(0, (duration_min - TIME_CUTOFF_MIN)) * TIME_RATE
    
    # Waiting time charge (higher rate for waiting)
    waiting_charge = max(0, (waiting_time_min - TIME_CUTOFF_MIN)) * (TIME_RATE * 1.5)
    
    return moving_time_charge + waiting_charge


def calculate_base_revenue(
    distance_km,
    duration_min,
    waiting_time_min=0,
    is_night=False
):
    """
    Calculate base revenue from ride components.
    This is the business-logic-only revenue (no ML).
    """
    
    revenue = BASE_FARE
    
    # Add distance component
    revenue += calculate_distance_charge(distance_km, is_night)
    
    # Add time component
    revenue += calculate_time_charge(duration_min, waiting_time_min)
    
    return revenue


# ============================================================================
# MAIN PRICING FUNCTION (IMPROVED)
# ============================================================================

def calculate_realistic_revenue(
    distance_km: float,
    duration_min: float,
    surge_multiplier: float = 1.0,
    zone_surge_multiplier: float = 1.0,
    is_morning_peak: bool = False,
    is_evening_peak: bool = False,
    is_night: bool = False,
    is_late_night: bool = False,
    is_weekend_noon: bool = False,
    is_raining: bool = False,
    weather_type: str = "clear",
    waiting_time_min: int = 0,
    total_km_today: float = 80,
    driver_rating: float = 4.5,
    is_female_driver: bool = False,
    ml_prediction: float = None,
    ml_weight: float = 0.25
) -> dict:
    """
    Calculate revenue using realistic ride-hailing pricing model.
    
    Args:
        - distance_km: Trip distance
        - duration_min: Trip duration
        - surge_multiplier: Uber's dynamic surge (1.0 = normal)
        - zone_surge_multiplier: Area-specific surge
        - Peak hour flags
        - is_night: After 10pm
        - Weather info
        - waiting_time_min: Pickup wait time
        - total_km_today: Driver's KM so far
        - driver_rating: 1-5 stars
        - is_female_driver: Gender-based incentives
        - ml_prediction: ML model prediction (if available)
        - ml_weight: How much to trust ML (0.0-0.5 recommended)
    
    Returns:
        dict with pricing breakdown
    """
    
    try:
        # ============ STEP 1: BASE REVENUE ============
        # Pure business logic (distance + time + waiting)
        base_revenue = calculate_base_revenue(
            distance_km,
            duration_min,
            waiting_time_min,
            is_night
        )
        
        # ============ STEP 2: APPLY MULTIPLIERS ============
        
        # Surge multiplier (with saturation curve)
        surge_factor = apply_surge_saturation(surge_multiplier)
        
        # Zone surge (cap at max)
        zone_surge = np.clip(zone_surge_multiplier, ZONE_SURGE_MIN, ZONE_SURGE_MAX)
        
        # Combined surge (multiplicative)
        total_surge = surge_factor * zone_surge
        
        # Peak hour multiplier
        peak_factor = get_peak_multiplier(
            is_morning_peak,
            is_evening_peak,
            is_late_night,
            is_weekend_noon
        )
        
        # Night multiplier (overlays with other multipliers)
        night_factor = NIGHT_MULTIPLIER if is_night else 1.0
        
        # Weather multiplier
        weather_factor = WEATHER_MULTIPLIERS.get(weather_type.lower(), 1.0)
        if is_raining:
            weather_factor = max(weather_factor, WEATHER_MULTIPLIERS.get("light_rain", 1.15))
        
        # Apply all multipliers (additive for peaks, multiplicative for others)
        # Formula: base * surge * max(peak, night) * weather
        # (peak and night don't stack since they're overlapping times)
        
        surge_applied = base_revenue * total_surge
        time_multiplier = max(peak_factor, night_factor)
        final_with_multipliers = surge_applied * time_multiplier * weather_factor
        
        # ============ STEP 3: ML ADJUSTMENT (Optional) ============
        
        revenue_before_ml = final_with_multipliers
        
        if ml_prediction is not None and ml_weight > 0:
            # Weight: (1 - ml_weight) business logic + ml_weight ML prediction
            # This allows ML to have influence while staying grounded in rules
            final_revenue = (
                (1 - ml_weight) * final_with_multipliers +
                ml_weight * ml_prediction
            )
        else:
            final_revenue = final_with_multipliers
        
        # ============ STEP 4: DRIVER INCENTIVES ============
        
        # Completion bonus (if target km reached)
        bonus_km_amount = max(0, total_km_today - DAILY_KM_TARGET) * BONUS_RATE_PER_KM
        
        # Rating bonus (higher rated drivers get small bonus)
        # Formula: 1 + (rating - 4.0) * 0.025 for 4+ stars
        rating_factor = 1.0
        if driver_rating >= 4.0:
            rating_factor = 1.0 + (driver_rating - 4.0) * 0.05  # 0-5% bonus
        
        # Female driver bonus (inclusivity)
        female_factor = FEMALE_DRIVER_BONUS if is_female_driver else 1.0
        
        # Apply driver-specific bonuses
        final_revenue = final_revenue * rating_factor * female_factor
        
        final_revenue += bonus_km_amount
        
        # ============ STEP 5: VALIDATION & BOUNDS ============
        
        # Ensure minimum revenue (ride always worth at least something)
        final_revenue = max(50, final_revenue)
        
        # Sanity check: max revenue (prevent extreme outliers)
        max_possible = base_revenue * SURGE_LEVELS["critical"] * NIGHT_MULTIPLIER * 1.5 * 1.5
        final_revenue = min(final_revenue, max_possible)
        
        # ============ RETURN BREAKDOWN ============
        
        return {
            "base_fare": round(base_revenue, 2),
            "surge_multiplier": round(total_surge, 2),
            "peak_multiplier": round(time_multiplier, 2),
            "weather_multiplier": round(weather_factor, 2),
            "after_multipliers": round(revenue_before_ml, 2),
            "ml_prediction": round(ml_prediction, 2) if ml_prediction else None,
            "ml_weight": ml_weight,
            "driver_rating_factor": round(rating_factor, 3),
            "bonus_amount": round(bonus_km_amount, 2),
            "final_revenue": round(final_revenue, 2),
            "surge_level": get_surge_level(surge_multiplier)
        }
    
    except Exception as e:
        logger.error(f"❌ Pricing calculation failed: {str(e)}", exc_info=True)
        raise


# ============================================================================
# CONFIDENCE SCORING (Model-based, not magic)
# ============================================================================

def calculate_confidence_score(
    predicted_revenue: float,
    base_business_revenue: float,
    ml_predicted_revenue: float = None,
    prediction_std: float = None,
    distance_km: float = 5.0,
    model_r2: float = 0.75
) -> float:
    """
    Calculate meaningful confidence score based on:
    1. Model R² (training quality)
    2. Prediction vs business logic difference (variance)
    3. Prediction std dev (model uncertainty)
    4. Distance from training data mean
    
    Range: 0.3 (low confidence) to 0.95 (high confidence)
    """
    
    base_confidence = 0.3  # Floor
    
    # 1. Model quality component (0.0 to 0.4)
    # R² of 0.7 = 0.3 confidence bump, R² of 0.9 = 0.4 bump
    model_quality_component = min(0.4, max(0.0, (model_r2 - 0.5) * 0.8))
    
    # 2. Prediction stability (0.0 to 0.3)
    # Small difference between ML and business logic = high confidence
    if ml_predicted_revenue and base_business_revenue > 0:
        diff_ratio = abs(ml_predicted_revenue - base_business_revenue) / base_business_revenue
        # 0%diff=0.3, 20%diff=0.15, 50%diff=0.05
        stability_component = max(0.0, (1.0 - diff_ratio) * 0.3)
    else:
        stability_component = 0.15
    
    # 3. Model uncertainty component (0.0 to 0.2)
    # Low prediction std dev = confident model
    if prediction_std:
        # Assuming std is in similar range to revenue
        uncertainty_component = max(0.0, (1.0 - prediction_std / predicted_revenue) * 0.2)
    else:
        uncertainty_component = 0.1
    
    # 4. Distance from typical range (0.0 to 0.1)
    # Very short/long trips are less confident
    distance_component = 0.0
    if 2 <= distance_km <= 20:
        distance_component = 0.1
    elif 0.5 <= distance_km <= 50:
        distance_component = 0.05
    
    # Combine components (capped at 0.95)
    confidence = min(
        0.95,
        base_confidence +
        model_quality_component +
        stability_component +
        uncertainty_component +
        distance_component
    )
    
    return round(confidence, 2)


if __name__ == "__main__":
    # Test pricing
    test_price = calculate_realistic_revenue(
        distance_km=10,
        duration_min=20,
        surge_multiplier=1.5,
        zone_surge_multiplier=1.2,
        is_evening_peak=True,
        is_raining=False,
        ml_prediction=420,
        ml_weight=0.25
    )
    print("✅ Pricing Test:")
    print(test_price)
    
    # Test confidence
    conf = calculate_confidence_score(
        predicted_revenue=420,
        base_business_revenue=380,
        ml_predicted_revenue=420,
        model_r2=0.78,
        distance_km=10
    )
    print(f"✅ Confidence: {conf}")
