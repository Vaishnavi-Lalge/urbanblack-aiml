"""
pricing_calculator.py  —  DynamicPricingEngine (UrbanBlack)
===========================================================
Implements the full Urban Black fare structure with long-trip tiered rates.

Rate structure (locked):
  Base fare : ₹ 55 for first 1.5 km  (+ 5 % GST)
  After 1.5 km:
      < 15 km      →  ₹ 25 / km   (short / medium)
      15 – < 18 km →  ₹ 23 / km   (long trip tier-1)
      18 – < 20 km →  ₹ 22 / km   (long trip tier-2)
      ≥  20 km     →  ₹ 20 / km   (long trip tier-3)

  Waiting charges : first 5 min free → ₹ 2 / min
  Night surcharge : + 25 %  (22:00 – 05:59)
  Weather surge   : + 10–20 % (tiered by rainfall mm/hr)
  Demand surge    : ML model or rule-based fallback (multiplier on operational sub-total)
  Platform fee    : 5 % on pre-tax total
  GST             : 5 % on (pre-tax + platform fee)
  Toll            : added post-GST (pass-through, no tax)
"""

from datetime import datetime, timedelta, timezone

from app.models.schemas import PricingRequest, PricingResponse, FareBreakdown
from app.services.rule_based_surge import get_rule_based_surge_multiplier
from app.services.ml_surge_predictor import ml_predictor

# ── rate constants ────────────────────────────────────────────────────────────
_BASE_FARE       = 55.0
_BASE_KM         = 1.5

_RATE_SHORT      = 25.0   # < 15 km
_RATE_LONG_T1    = 23.0   # 15 ≤ km < 18
_RATE_LONG_T2    = 22.0   # 18 ≤ km < 20
_RATE_LONG_T3    = 20.0   # ≥ 20 km

_WAIT_FREE_MIN   = 5.0
_WAIT_RATE       = 2.0

_NIGHT_START     = 22
_NIGHT_END       = 6
_NIGHT_FACTOR    = 0.25

_WEATHER_HEAVY   = 10.0   # mm/hr → 20 % surge
_WEATHER_LIGHT   = 2.0    # mm/hr → 10 % surge
_WEATHER_HEAVY_F = 0.20
_WEATHER_LIGHT_F = 0.10

_PLATFORM_FEE_PCT = 0.05
_GST_PCT          = 0.05
# ─────────────────────────────────────────────────────────────────────────────


def _dist_rate(km: float) -> float:
    """Per-km rate for the incremental distance beyond 1.5 km."""
    if km < 15:  return _RATE_SHORT
    if km < 18:  return _RATE_LONG_T1
    if km < 20:  return _RATE_LONG_T2
    return _RATE_LONG_T3


def _is_night(hour: int, is_night_flag: bool) -> bool:
    return is_night_flag or hour >= _NIGHT_START or hour < _NIGHT_END


class PricingCalculator:

    async def calculate(self, request: PricingRequest) -> PricingResponse:
        km = float(request.estimated_distance_km)

        # ── 1. Distance fare (tiered long-trip rate) ─────────────────────────
        incremental_km = max(0.0, km - _BASE_KM)
        rate_per_km    = _dist_rate(km)
        distance_charge = incremental_km * rate_per_km
        base_distance_fare = _BASE_FARE + distance_charge   # before any surcharges

        # ── 2. Waiting charges ───────────────────────────────────────────────
        billable_wait = max(0.0, float(request.waiting_time_minutes) - _WAIT_FREE_MIN)
        waiting_charge = billable_wait * _WAIT_RATE

        # running sub-total (base fare components only, no surcharges yet)
        running_subtotal = base_distance_fare + waiting_charge

        # ── 3. Night surcharge  (+25 %) ──────────────────────────────────────
        night = _is_night(request.hour_of_day, request.is_night_trip)
        night_surcharge = base_distance_fare * _NIGHT_FACTOR if night else 0.0

        # ── 4. Weather surge (10 % or 20 % on base distance fare) ───────────
        rain_mm = float(request.rainfall_mm_per_hour)
        if rain_mm > _WEATHER_HEAVY:
            weather_surcharge = base_distance_fare * _WEATHER_HEAVY_F
        elif rain_mm > _WEATHER_LIGHT:
            weather_surcharge = base_distance_fare * _WEATHER_LIGHT_F
        else:
            weather_surcharge = 0.0

        operational_subtotal = running_subtotal + night_surcharge + weather_surcharge

        # ── 5. Demand surge (ML or rule-based) ───────────────────────────────
        if ml_predictor.model is not None:
            surge_multiplier = ml_predictor.predict_surge(request)
        else:
            surge_multiplier, _ = get_rule_based_surge_multiplier(
                request.zone_demand_supply_ratio
            )

        # Hard-cap at 2.5×
        surge_multiplier = min(surge_multiplier, 2.5)
        is_surge_capped  = surge_multiplier >= 2.5

        if   surge_multiplier < 1.2:  surge_tier = "normal"
        elif surge_multiplier < 1.6:  surge_tier = "mild"
        elif surge_multiplier < 2.2:  surge_tier = "moderate"
        elif surge_multiplier < 2.5:  surge_tier = "peak"
        else:                          surge_tier = "capped"

        demand_surge_amount = operational_subtotal * max(0.0, surge_multiplier - 1.0)
        pre_fee_total       = operational_subtotal + demand_surge_amount

        # ── 6. Platform fee (5 %) + GST (5 % on pre-fee + platform fee) ──────
        platform_fee  = pre_fee_total * _PLATFORM_FEE_PCT
        taxable_amount = pre_fee_total + platform_fee
        gst_amount    = taxable_amount * _GST_PCT

        # ── 7. Toll (pass-through, post-tax) ─────────────────────────────────
        final_fare = taxable_amount + gst_amount + float(request.toll_cost_estimate)

        # ── Breakdown ─────────────────────────────────────────────────────────
        breakdown = FareBreakdown(
            base_fare           = round(_BASE_FARE, 2),
            distance_charge     = round(distance_charge, 2),
            waiting_charge      = round(waiting_charge, 2),
            night_surcharge     = round(night_surcharge, 2),
            weather_surcharge   = round(weather_surcharge, 2),
            demand_surge_amount = round(demand_surge_amount, 2),
            toll_component      = round(request.toll_cost_estimate, 2),
            platform_fee        = round(platform_fee, 2),
            gst_amount          = round(gst_amount, 2),
        )

        banner_map = {
            "normal":   "Standard fare",
            "mild":     "High demand — slight surge",
            "moderate": "Very high demand",
            "peak":     "Peak surge active",
            "capped":   "Surge cap reached",
        }

        return PricingResponse(
            request_id        = request.request_id,
            surge_multiplier  = round(surge_multiplier, 2),
            surge_tier        = surge_tier,
            final_fare        = round(final_fare, 2),
            fare_breakdown    = breakdown,
            currency          = "INR",
            fare_valid_until  = datetime.now(timezone.utc) + timedelta(minutes=2),
            surge_banner_text = banner_map.get(surge_tier, "Standard fare"),
            is_surge_capped   = is_surge_capped,
            # extra debug fields (optional, strip in prod if schema disallows)
            rate_per_km_used  = rate_per_km,
            fare_slab         = (1 if km < 15 else 2 if km < 18 else 3 if km < 20 else 4),
            is_long_trip      = km >= 15,
        )
