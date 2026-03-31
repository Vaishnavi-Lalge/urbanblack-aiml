from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_price(
    base_prediction,
    distance_km,
    duration_min,
    total_km_today,
    surge_multiplier=1.0,
    zone_surge_multiplier=1.0,  # 🔥 ADD THIS
    is_night=False,
    is_raining=False,
    waiting_time_min=0
):
    try:
        # ---------------- BASE ----------------
        base_fare = 55

        extra_km = max(0, distance_km - 1.5)
        distance_charge = extra_km * 25

        fare = base_fare + distance_charge

        # ---------------- WAITING ----------------
        waiting_charge = max(0, waiting_time_min - 5) * 2
        fare += waiting_charge

        # ---------------- SURGE (FIXED) ----------------
        total_surge = surge_multiplier * zone_surge_multiplier
        fare *= total_surge

        # ---------------- NIGHT ----------------
        if is_night:
            fare *= 1.25

        # ---------------- WEATHER ----------------
        if is_raining:
            fare *= 1.15

        # ---------------- BONUS ----------------
        bonus = max(0, total_km_today - 135) * 12

        # ---------------- ML (REDUCED IMPACT) ----------------
        # 🔥 FINAL FIX: ML only 10%
        adjusted_fare = (0.9 * fare) + (0.1 * base_prediction)

        final_revenue = adjusted_fare + bonus

        logger.info(f"💰 Final Revenue: {final_revenue}")

        return {
            "fare_before_adjustment": round(fare, 2),
            "ml_prediction": round(base_prediction, 2),
            "final_revenue": round(final_revenue, 2)
        }

    except Exception as e:
        logger.error(f"❌ Pricing calculation failed: {str(e)}", exc_info=True)
        raise