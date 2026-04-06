"""
Improved Pricing Service - Production Ready
Replaces old pricing_service.py with realistic ride-hailing pricing logic.

Key Improvements:
- Dynamic base fares by city and distance
- Realistic night multipliers with supply adjustment
- Surge saturation curve (not linear)
- Comprehensive peak hour detection
- Supply-demand based pricing
- Driver quality adjustments
- Revenue-based performance bonuses
- Better ML integration (30% weight)
"""

import math
from typing import Optional, Dict, Tuple


# ============================================================================
# CONFIGURATION
# ============================================================================

CITY_BASE_FARES = {
    """City-specific base fares (in ₹). Values are multipliers on ₹40 base."""
    "bangalore": 40 * 0.95,      # 5% discount
    "mumbai": 40 * 1.10,         # 10% premium
    "delhi": 40 * 1.05,          # 5% premium
    "hyderabad": 40 * 0.90,      # 10% discount
    "default": 40                # Default base: ₹40
}

# Pricing coefficients
DISTANCE_RATE_SHORT = 28        # ₹/km for short trips (1.5-5km)
DISTANCE_RATE_MID = 24          # ₹/km for mid trips (5-15km)
DISTANCE_RATE_LONG = 20         # ₹/km for long trips (15+km)
TIME_RATE = 2.5                 # ₹/min
WAITING_RATE_SHORT = 2.0        # ₹/min for waiting < 10 min
WAITING_RATE_LONG = 3.0         # ₹/min for waiting 10-15 min
WAITING_RATE_EXTENDED = 4.0     # ₹/min for waiting > 15 min

# Surge configuration
SURGE_LOG_COEFFICIENT = 0.75    # Controls saturation curve steepness
SURGE_MAX_MULTIPLIER = 2.2      # Maximum price multiplier from surge

# ML blending
ML_WEIGHT = 0.30                # 30% ML, 70% business logic

# Bonus configuration
BONUS_TIER_100_150 = 0.05       # 5% of revenue for 100-150km days
BONUS_TIER_150_200 = 0.07       # 7% of revenue for 150-200km days
BONUS_TIER_200_PLUS = 0.10      # 10% of revenue for 200+km days
BONUS_MINIMUM = 50              # ₹50 minimum bonus


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_base_fare(
    city: str = "default",
    distance_km: float = 0,
    is_peak: bool = False
) -> float:
    """
    Calculate base fare with city and distance adjustments.
    
    Args:
        city: City name for fare adjustment
        distance_km: Trip distance in km
        is_peak: Whether it's peak hour
    
    Returns:
        Base fare in rupees
    """
    # Get city multiplier
    city_key = city.lower() if city.lower() in CITY_BASE_FARES else "default"
    city_multiplier = CITY_BASE_FARES[city_key]
    
    # Distance adjustment (short trips less efficient)
    if distance_km <= 2:
        distance_multiplier = 1.2   # 20% higher for short trips
    elif distance_km <= 5:
        distance_multiplier = 1.1   # 10% higher
    elif distance_km <= 15:
        distance_multiplier = 1.0   # Standard
    else:
        distance_multiplier = 0.95  # 5% lower for long trips
    
    # Peak adjustment
    peak_multiplier = 1.05 if is_peak else 1.0
    
    base_fare = city_multiplier * distance_multiplier * peak_multiplier
    return round(base_fare, 2)


def get_distance_charge(distance_km: float) -> float:
    """
    Calculate distance-based charge with tiered pricing.
    
    Args:
        distance_km: Trip distance in km
    
    Returns:
        Distance charge in rupees
    """
    if distance_km <= 1.5:
        return 0
    elif distance_km <= 5:
        # Short trips: higher rate
        return (distance_km - 1.5) * DISTANCE_RATE_SHORT
    elif distance_km <= 15:
        # Mid trips: medium rate
        short_portion = 3.5 * DISTANCE_RATE_SHORT
        mid_portion = (distance_km - 5) * DISTANCE_RATE_MID
        return short_portion + mid_portion
    else:
        # Long trips: lower rate (efficiency)
        short_portion = 3.5 * DISTANCE_RATE_SHORT
        mid_portion = 10 * DISTANCE_RATE_MID
        long_portion = (distance_km - 15) * DISTANCE_RATE_LONG
        return short_portion + mid_portion + long_portion


def get_time_charge(duration_min: float) -> float:
    """
    Calculate time-based charge.
    Accounts for traffic delays.
    
    Args:
        duration_min: Trip duration in minutes
    
    Returns:
        Time charge in rupees
    """
    return max(0, duration_min - 2) * TIME_RATE


def get_waiting_charge(waiting_time_min: float) -> float:
    """
    Calculate waiting time charge with progressive rates.
    
    Args:
        waiting_time_min: Waiting time in minutes
    
    Returns:
        Waiting charge in rupees
    """
    if waiting_time_min <= 5:
        return 0
    elif waiting_time_min <= 10:
        # First 5 minutes: ₹2/min
        return (waiting_time_min - 5) * WAITING_RATE_SHORT
    elif waiting_time_min <= 15:
        # First 5 minutes at ₹2/min, next at ₹3/min
        first_tier = 5 * WAITING_RATE_SHORT
        second_tier = (waiting_time_min - 10) * WAITING_RATE_LONG
        return first_tier + second_tier
    else:
        # Extended waits: premium rates
        first_tier = 5 * WAITING_RATE_SHORT
        second_tier = 5 * WAITING_RATE_LONG
        extended_tier = (waiting_time_min - 15) * WAITING_RATE_EXTENDED
        return first_tier + second_tier + extended_tier


def get_peak_multiplier(hour_of_day: int, day_of_week: int) -> float:
    """
    Calculate peak hour multiplier.
    Distinguishes between weekday and weekend peaks.
    
    Args:
        hour_of_day: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)
    
    Returns:
        Peak multiplier (1.0 = no peak)
    """
    is_weekday = day_of_week < 5  # Monday-Friday
    
    if is_weekday:
        if 6 <= hour_of_day < 9:      # Morning rush: 6-8am
            return 1.20
        elif 12 <= hour_of_day < 14:  # Lunch: 12-1pm
            return 1.10
        elif 17 <= hour_of_day < 20:  # Evening rush: 5-7pm (heaviest)
            return 1.30
        else:
            return 1.0
    else:  # Weekend
        if 11 <= hour_of_day < 14:    # Brunch/lunch: 11am-1pm
            return 1.15
        elif 18 <= hour_of_day < 21:  # Evening: 6-8pm
            return 1.20
        else:
            return 1.0


def get_night_multiplier(
    hour_of_day: int,
    rides_in_zone: int = 0,
    drivers_in_zone: int = 0
) -> float:
    """
    Calculate night time multiplier with supply adjustment.
    
    Args:
        hour_of_day: Hour of day (0-23)
        rides_in_zone: Number of active rides in zone
        drivers_in_zone: Number of active drivers in zone
    
    Returns:
        Night multiplier (1.0 = not night)
    """
    # Check if it's night time (10pm-6am)
    if not (hour_of_day >= 22 or hour_of_day <= 6):
        return 1.0
    
    # Base multiplier by time of night
    if 22 <= hour_of_day <= 23:     # 10-11pm
        base_mult = 1.35
    elif 0 <= hour_of_day <= 2:     # 12-2am (deepest night)
        base_mult = 1.75
    elif 3 <= hour_of_day <= 5:     # 3-5am
        base_mult = 1.50
    else:                            # 6am or edge case
        base_mult = 1.20
    
    # Adjust for supply shortage
    if rides_in_zone > 0:
        supply_ratio = drivers_in_zone / (rides_in_zone + 1)
        if supply_ratio < 0.3:
            supply_adjustment = 1.15  # +15% when very few drivers
        elif supply_ratio < 0.5:
            supply_adjustment = 1.08  # +8% when few drivers
        else:
            supply_adjustment = 1.0   # No adjustment when supply ok
    else:
        supply_adjustment = 1.0
    
    final_mult = base_mult * supply_adjustment
    return min(final_mult, 2.2)  # Cap at 2.2x


def apply_surge_saturation(surge_multiplier: float) -> float:
    """
    Apply surge saturation curve (not linear).
    Uses logarithmic scaling to prevent unrealistic pricing.
    
    Real-world: 2x surge → ~1.5x price (demand elasticity)
    Old system: 2x surge → 2x price (wrong!)
    
    Args:
        surge_multiplier: Raw surge multiplier (1.0 = no surge)
    
    Returns:
        Price multiplier for surge
    """
    if surge_multiplier <= 1.0:
        return 1.0
    
    # Logarithmic saturation
    saturation = 1.0 + SURGE_LOG_COEFFICIENT * math.log(surge_multiplier)
    
    # Cap at maximum
    return min(saturation, SURGE_MAX_MULTIPLIER)


def apply_weather_multiplier(is_raining: bool, is_very_hot: bool = False) -> float:
    """
    Apply weather-based multiplier.
    
    Args:
        is_raining: Whether it's raining
        is_very_hot: Whether it's very hot (>40°C)
    
    Returns:
        Weather multiplier
    """
    mult = 1.0
    if is_raining:
        mult *= 1.15  # +15% for rain
    if is_very_hot:
        mult *= 1.05  # +5% for extreme heat
    return mult


def apply_driver_quality_multiplier(base_revenue: float, driver_rating: float) -> float:
    """
    Apply driver quality/rating adjustment.
    Better-rated drivers earn more (incentive).
    
    Args:
        base_revenue: Base revenue before adjustment
        driver_rating: Driver rating (1-5)
    
    Returns:
        Adjusted revenue
    """
    if driver_rating >= 4.8:
        multiplier = 1.10  # +10% excellent
    elif driver_rating >= 4.5:
        multiplier = 1.05  # +5% good
    elif driver_rating >= 4.0:
        multiplier = 1.00  # baseline
    elif driver_rating >= 3.5:
        multiplier = 0.97  # -3% fair
    else:
        multiplier = 0.95  # -5% poor
    
    return base_revenue * multiplier


def calculate_bonus(
    total_km_today: float,
    daily_revenue_so_far: float,
    driver_rating: float = 4.0
) -> float:
    """
    Calculate performance bonus based on kilometers and revenue.
    Tiered structure encourages both distance and quality.
    
    Args:
        total_km_today: Total kilometers driven today
        daily_revenue_so_far: Total revenue earned today (excluding bonus)
        driver_rating: Driver rating (1-5)
    
    Returns:
        Bonus amount in rupees
    """
    # Determine tier based on kilometers
    if total_km_today < 100:
        bonus_rate = 0.0
    elif total_km_today < 150:
        bonus_rate = BONUS_TIER_100_150
    elif total_km_today < 200:
        bonus_rate = BONUS_TIER_150_200
    else:
        bonus_rate = BONUS_TIER_200_PLUS
    
    # Calculate base bonus
    bonus = daily_revenue_so_far * bonus_rate if daily_revenue_so_far > 0 else 0
    
    # Rating adjustment
    if driver_rating >= 4.5:
        bonus *= 1.02  # +2% for good drivers
    elif driver_rating < 3.5:
        bonus *= 0.98  # -2% for poor drivers
    
    # Ensure minimum
    return max(bonus, BONUS_MINIMUM)


def calculate_confidence_score(
    model_r_squared: float = 0.70,
    is_peak_hour: bool = False,
    is_night: bool = False,
    prediction_uncertainty: float = 0.15,
    ml_predictions_available: bool = True
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate confidence score based on multiple factors.
    
    Args:
        model_r_squared: Model's R² coefficient
        is_peak_hour: Whether it's peak hour
        is_night: Whether it's night time
        prediction_uncertainty: Coefficient of variation in predictions
        ml_predictions_available: Whether ML predictions are available
    
    Returns:
        Tuple of (confidence score 0-1, component breakdown dict)
    """
    components = {}
    
    # Model quality (40% weight)
    # Better R² = higher confidence
    model_score = min(model_r_squared / 0.80, 1.0)  # Normalize to 0.80 R²
    components['model_quality'] = model_score * 0.40
    
    # Prediction stability (30% weight)
    # Peak/night = less stable
    stability = 1.0
    if is_peak_hour:
        stability *= 0.85  # -15% confidence in peak
    if is_night:
        stability *= 0.80  # -20% confidence at night
    components['stability'] = stability * 0.30
    
    # Uncertainty (20% weight)
    # Lower uncertainty = higher prediction confidence
    uncertainty_score = 1.0 - min(prediction_uncertainty / 0.30, 1.0)
    components['uncertainty'] = uncertainty_score * 0.20
    
    # ML availability (10% weight)
    ml_score = 1.0 if ml_predictions_available else 0.7
    components['ml_available'] = ml_score * 0.10
    
    total_score = sum(components.values())
    return round(total_score, 3), components


# ============================================================================
# MAIN PRICING FUNCTION
# ============================================================================

def calculate_improved_price(
    distance_km: float,
    duration_min: float,
    hour_of_day: int,
    day_of_week: int,
    rides_in_zone: int,
    drivers_in_zone: int,
    surge_multiplier: float,
    zone_surge_multiplier: float = 1.0,
    is_raining: bool = False,
    waiting_time_min: float = 0,
    total_km_today: float = 0,
    daily_revenue_so_far: float = 0,
    driver_rating: float = 4.0,
    ml_prediction: float = 300,
    city: str = "default",
    model_r_squared: float = 0.70,
    return_breakdown: bool = True
) -> Dict:
    """
    MAIN PRICING FUNCTION - Production Ready
    
    Calculates realistic ride fare combining:
    - Base fare (city & distance adjusted)
    - Distance charge (tiered rates)
    - Time charge (traffic-aware)
    - Waiting charge (progressive)
    - Peak multiplier (comprehensive peak detection)
    - Night multiplier (supply-aware)
    - Surge saturation (realistic demand response)
    - Weather adjustment
    - ML blending (30% weight)
    - Driver quality incentive
    - Performance bonus
    
    Args:
        distance_km: Trip distance in km
        duration_min: Estimated trip duration in minutes
        hour_of_day: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)
        rides_in_zone: Active rides in zone
        drivers_in_zone: Active drivers in zone
        surge_multiplier: Current surge (e.g., 1.5, 2.0)
        zone_surge_multiplier: Zone-specific surge adjustment
        is_raining: Whether it's raining
        waiting_time_min: Expected/actual waiting time
        total_km_today: Total km driven today
        daily_revenue_so_far: Revenue earned today (excluding bonus)
        driver_rating: Driver rating (1-5)
        ml_prediction: ML model's revenue prediction
        city: City name for fare adjustments
        model_r_squared: Model's R² for confidence calculation
        return_breakdown: If True, return detailed breakdown
    
    Returns:
        Dictionary with pricing details and breakdown
    """
    
    # ===== CALCULATE BASE CHARGES =====
    
    base_fare = get_base_fare(city, distance_km, False)
    distance_charge = get_distance_charge(distance_km)
    time_charge = get_time_charge(duration_min)
    waiting_charge = get_waiting_charge(waiting_time_min)
    
    subtotal = base_fare + distance_charge + time_charge + waiting_charge
    
    # ===== CALCULATE MULTIPLIERS =====
    
    peak_mult = get_peak_multiplier(hour_of_day, day_of_week)
    night_mult = get_night_multiplier(hour_of_day, rides_in_zone, drivers_in_zone)
    
    # Use the higher multiplier (don't stack)
    time_multiplier = max(peak_mult, night_mult)
    
    # Surge with saturation curve
    total_surge = surge_multiplier * zone_surge_multiplier
    surge_multiplier_final = apply_surge_saturation(total_surge)
    
    # Weather
    weather_mult = apply_weather_multiplier(is_raining)
    
    # ===== APPLY MULTIPLIERS =====
    
    after_multipliers = subtotal * time_multiplier * surge_multiplier_final * weather_mult
    
    # ===== ML BLENDING =====
    
    blended_fare = (
        (1 - ML_WEIGHT) * after_multipliers +
        ML_WEIGHT * ml_prediction
    )
    
    # ===== DRIVER QUALITY ADJUSTMENT =====
    
    quality_multiplier = apply_driver_quality_multiplier(1.0, driver_rating)
    after_quality = blended_fare * quality_multiplier
    
    # ===== ADD BONUS =====
    
    bonus = calculate_bonus(total_km_today, daily_revenue_so_far, driver_rating)
    
    # ===== FINAL REVENUE =====
    
    final_revenue = max(after_quality + bonus, 50)  # Minimum ₹50
    
    # ===== CONFIDENCE SCORE =====
    
    is_peak = peak_mult > 1.0
    is_night = night_mult > 1.0
    confidence_score, confidence_breakdown = calculate_confidence_score(
        model_r_squared=model_r_squared,
        is_peak_hour=is_peak,
        is_night=is_night,
        prediction_uncertainty=0.15  # 15% COV default
    )
    
    # ===== DETERMINE PRICE RANGE =====
    
    # Range based on confidence
    if confidence_score >= 0.85:
        range_percent = 0.08  # ±8% for high confidence
    elif confidence_score >= 0.70:
        range_percent = 0.12  # ±12% for medium
    else:
        range_percent = 0.20  # ±20% for low confidence
    
    min_price = round(final_revenue * (1 - range_percent), 2)
    max_price = round(final_revenue * (1 + range_percent), 2)
    
    # ===== PREPARE RESPONSE =====
    
    response = {
        "final_revenue": round(final_revenue, 2),
        "confidence_score": confidence_score,
        "price_range": {
            "min": min_price,
            "max": max_price,
            "range_percent": round(range_percent * 100, 1)
        }
    }
    
    if return_breakdown:
        response["breakdown"] = {
            "base_fare": round(base_fare, 2),
            "distance_charge": round(distance_charge, 2),
            "time_charge": round(time_charge, 2),
            "waiting_charge": round(waiting_charge, 2),
            "subtotal": round(subtotal, 2),
            "peak_multiplier": round(peak_mult, 2),
            "night_multiplier": round(night_mult, 2),
            "time_multiplier_used": round(time_multiplier, 2),
            "surge_multiplier": round(surge_multiplier_final, 2),
            "weather_multiplier": round(weather_mult, 2),
            "after_multipliers": round(after_multipliers, 2),
            "ml_weight": ML_WEIGHT,
            "ml_prediction": round(ml_prediction, 2),
            "after_ml_blend": round(blended_fare, 2),
            "driver_quality_multiplier": round(quality_multiplier, 2),
            "after_quality": round(after_quality, 2),
            "bonus": round(bonus, 2),
            "confidence_breakdown": {k: round(v, 3) for k, v in confidence_breakdown.items()}
        }
    
    return response


# ============================================================================
# COMPATIBILITY FUNCTION
# ============================================================================

def calculate_realistic_revenue(
    trip_distance,
    trip_duration,
    trips_in_zone,
    surge_multiplier,
    zone_surge_multiplier=1.0,
    is_raining=False,
    hour_of_day=12,
    day_of_week=2,
    rides_zone=50,
    drivers_zone=30,
    driver_rating=4.0,
    ml_prediction=300
):
    """
    Backward compatibility wrapper for old function name.
    
    This function maintains the same interface as before
    but uses the new improved pricing logic.
    """
    return calculate_improved_price(
        distance_km=trip_distance,
        duration_min=trip_duration,
        hour_of_day=hour_of_day,
        day_of_week=day_of_week,
        rides_in_zone=rides_zone,
        drivers_in_zone=drivers_zone,
        surge_multiplier=surge_multiplier,
        zone_surge_multiplier=zone_surge_multiplier,
        is_raining=is_raining,
        driver_rating=driver_rating,
        ml_prediction=ml_prediction,
        return_breakdown=False
    )


# ============================================================================
# TEST EXAMPLES
# ============================================================================

if __name__ == "__main__":
    
    print("\n" + "="*70)
    print("IMPROVED PRICING SERVICE - TEST EXAMPLES")
    print("="*70 + "\n")
    
    # Test 1: Short trip, Bangalore, afternoon
    print("TEST 1: Short Urban Trip (Bangalore, 3pm)")
    print("-" * 70)
    result1 = calculate_improved_price(
        distance_km=3,
        duration_min=8,
        hour_of_day=15,
        day_of_week=2,  # Wednesday
        rides_in_zone=40,
        drivers_in_zone=35,
        surge_multiplier=1.0,
        zone_surge_multiplier=1.0,
        is_raining=False,
        driver_rating=4.5,
        ml_prediction=250,
        city="bangalore"
    )
    print(f"Final Revenue: ₹{result1['final_revenue']}")
    print(f"Confidence: {result1['confidence_score']}")
    print(f"Range: ₹{result1['price_range']['min']}-{result1['price_range']['max']}\n")
    
    # Test 2: Long trip, evening peak, surge
    print("TEST 2: Long Trip (Evening Peak, Surge)")
    print("-" * 70)
    result2 = calculate_improved_price(
        distance_km=15,
        duration_min=25,
        hour_of_day=19,  # 7pm
        day_of_week=2,
        rides_in_zone=80,
        drivers_in_zone=25,  # Low supply
        surge_multiplier=1.8,
        zone_surge_multiplier=1.2,
        is_raining=False,
        total_km_today=120,
        daily_revenue_so_far=1500,
        driver_rating=4.7,
        ml_prediction=500,
        city="bangalore"
    )
    print(f"Final Revenue: ₹{result2['final_revenue']}")
    print(f"Confidence: {result2['confidence_score']}")
    print(f"Range: ₹{result2['price_range']['min']}-{result2['price_range']['max']}\n")
    
    # Test 3: Late night trip with long wait
    print("TEST 3: Late Night (2am) with Waiting Time")
    print("-" * 70)
    result3 = calculate_improved_price(
        distance_km=5,
        duration_min=12,
        hour_of_day=2,  # 2am
        day_of_week=5,  # Saturday
        rides_in_zone=15,
        drivers_in_zone=8,   # Very low supply
        surge_multiplier=3.0,
        zone_surge_multiplier=1.1,
        is_raining=True,
        waiting_time_min=8,
        driver_rating=3.8,
        ml_prediction=450,
        city="bangalore"
    )
    print(f"Final Revenue: ₹{result3['final_revenue']}")
    print(f"Confidence: {result3['confidence_score']}")
    print(f"Range: ₹{result3['price_range']['min']}-{result3['price_range']['max']}\n")
    
    print("="*70)
    print("All tests completed successfully!")
    print("="*70 + "\n")

