from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_price(
    base_prediction,
    distance_km,
    duration_min,
    total_km_today,
    surge_multiplier=1.0,
    zone_surge_multiplier=1.0,
    is_night=False,
    is_raining=False,
    waiting_time_min=0
):
    """
    Industry-grade pricing calculation following Ola/Uber standards.
    
    Components:
    1. Base Fare (fixed)
    2. Distance Charge (₹/km)
    3. Time Charge (₹/minute)
    4. Waiting Charge (after 5 min free)
    5. Surge Multiplier (demand-based)
    6. Night Premium
    7. Weather Premium
    8. Booking Fee
    """
    try:
        # ============ REAL-WORLD PRICING FORMULA ============
        
        # 📍 PHASE 1: BASE COMPONENTS
        base_fare = 55  # Initial fixed charge (₹)
        booking_fee = 8  # Always charged (₹)
        
        # 📏 PHASE 2: DISTANCE CHARGE
        # Most rides have 1.5 km minimum
        min_distance_km = 1.5
        distance_per_km = 28  # ₹/km (Ola/Uber standard)
        
        if distance_km <= min_distance_km:
            distance_charge = base_fare  # Base fare covers first 1.5 km
        else:
            extra_km = distance_km - min_distance_km
            distance_charge = base_fare + (extra_km * distance_per_km)
        
        # ⏱️ PHASE 3: TIME CHARGE
        # Industry standard: 1-2 ₹/minute for active ride
        time_per_minute = 1.8  # ₹/minute (realistic average)
        time_charge = duration_min * time_per_minute
        
        # 🚗 PHASE 4: WAITING CHARGE (after 5 min free wait)
        waiting_per_minute = 2.0  # ₹/minute after 5 min buffer
        free_waiting_min = 5
        
        if waiting_time_min > free_waiting_min:
            waiting_charge = (waiting_time_min - free_waiting_min) * waiting_per_minute
        else:
            waiting_charge = 0
        
        # Base price before multipliers
        base_price = distance_charge + time_charge + waiting_charge + booking_fee
        
        # 🔶 PHASE 5: SURGE MULTIPLIER (demand-based)
        # Combines driver shortage and ride demand
        total_surge = surge_multiplier * zone_surge_multiplier
        surge_price = base_price * total_surge
        
        # 🌙 PHASE 6: NIGHT PREMIUM (10 PM - 6 AM)
        # Industry standard: 25-50% premium
        night_multiplier = 1.35 if is_night else 1.0  # 35% premium
        
        # 🌧️ PHASE 7: WEATHER PREMIUM (rain/snow/extreme weather)
        # Industry standard: 10-20% premium
        weather_multiplier = 1.15 if is_raining else 1.0  # 15% premium
        
        # Calculate final fare before incentives
        final_fare = surge_price * night_multiplier * weather_multiplier
        
        # ✅ PHASE 8: INCENTIVES & BONUSES
        # Driver incentive: Complete X km in shift for bonus
        incentive_threshold_km = 135
        incentive_per_km = 12
        
        if total_km_today >= incentive_threshold_km:
            bonus_km = total_km_today - incentive_threshold_km
            bonus = bonus_km * incentive_per_km
        else:
            bonus = 0
        
        # 🎯 PHASE 9: FINAL REVENUE
        # Real-world cap: ensure reasonable revenue
        final_revenue = final_fare + bonus
        
        # Minimum revenue guard (avoid unrealistic low values)
        final_revenue = max(50, final_revenue)
        
        # Maximum revenue guard (avoid unbounded surge)
        # Cap surge to max 3.5x with all multipliers
        max_possible = base_price * 3.5
        final_revenue = min(final_revenue, max_possible + bonus)
        
        logger.info(
            f"💰 Revenue Breakdown:\n"
            f"   Distance: ₹{distance_charge:.2f} ({distance_km:.1f} km)\n"
            f"   Time: ₹{time_charge:.2f} ({duration_min:.0f} min)\n"
            f"   Waiting: ₹{waiting_charge:.2f}\n"
            f"   Surge: {total_surge:.2f}x\n"
            f"   Night: {night_multiplier:.2f}x | Weather: {weather_multiplier:.2f}x\n"
            f"   Bonus: ₹{bonus:.2f}\n"
            f"   TOTAL: ₹{final_revenue:.2f}"
        )
        
        return {
            "base_price": round(base_price, 2),
            "distance_charge": round(distance_charge, 2),
            "time_charge": round(time_charge, 2),
            "waiting_charge": round(waiting_charge, 2),
            "booking_fee": booking_fee,
            "surge_multiplier": round(total_surge, 2),
            "night_multiplier": round(night_multiplier, 2),
            "weather_multiplier": round(weather_multiplier, 2),
            "bonus": round(bonus, 2),
            "final_revenue": round(final_revenue, 2)
        }

    except Exception as e:
        logger.error(f"❌ Pricing calculation failed: {str(e)}", exc_info=True)
        raise