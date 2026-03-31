"""
fare_calculator.py
Urban Black — canonical fare engine for LongTripOpt.

Fare rules (as per business spec):
────────────────────────────────────────────────────────
Base fare    : ₹55 for first 1.5 km  (+5% GST)
After 1.5 km :
   < 15 km       →  ₹25/km  (short / medium trip)
   15 – <18 km   →  ₹23/km  (long trip tier-1)
   18 – <20 km   →  ₹22/km  (long trip tier-2)
   ≥  20 km      →  ₹20/km  (long trip tier-3)

Waiting      : First 5 min free → ₹2/min thereafter
Night        : +25%  (22:00–05:59)
Weather surge: +10–20% (weather_surge multiplier, e.g. 1.15)
Premium (AC) : +10% on distance fare
GST          : 5% on full sub-total

Driver shift constraints (enforced at dispatch, not here):
  Min rides/shift : 25
  Shift duration  : 12 h
  Min distance    : 135 km
────────────────────────────────────────────────────────
"""
from __future__ import annotations
import math, random

# ── rate constants ────────────────────────────────────
BASE_FARE_FIXED    = 55.0   # ₹ for first 1.5 km
BASE_KM_INCLUDED   = 1.5

RATE_SHORT         = 25.0   # < 15 km
RATE_LONG_T1       = 23.0   # 15 ≤ km < 18
RATE_LONG_T2       = 22.0   # 18 ≤ km < 20
RATE_LONG_T3       = 20.0   # ≥ 20 km

WAIT_FREE_MIN      = 5.0
WAIT_RATE          = 2.0    # ₹/min after free window
NIGHT_FACTOR       = 0.25   # +25%
PREMIUM_FACTOR     = 0.10   # +10% for AC
GST_RATE           = 0.05   # 5%

NIGHT_START        = 22
NIGHT_END          = 6
# ─────────────────────────────────────────────────────

def _rate_for_km(km: float) -> float:
    if km < 15:   return RATE_SHORT
    if km < 18:   return RATE_LONG_T1
    if km < 20:   return RATE_LONG_T2
    return RATE_LONG_T3

def _is_night(hour: int) -> bool:
    return hour >= NIGHT_START or hour < NIGHT_END

def compute_fare(
    km: float,
    is_ac: bool,
    trip_type: str,
    hour: int,
    wait_time_min: float = 0.0,
    weather_surge: float = 1.0,
    is_holiday: bool = False,
    noise_pct: float = 0.0,
) -> dict:
    """
    Compute the full Urban Black fare breakdown.
    Returns a dict with offered_fare and every component.
    """
    km = max(0.0, float(km))

    # 1. Distance fare
    incremental_km = max(0.0, km - BASE_KM_INCLUDED)
    rate_per_km    = _rate_for_km(km)
    distance_fare  = BASE_FARE_FIXED + incremental_km * rate_per_km
    if is_ac:
        distance_fare *= (1.0 + PREMIUM_FACTOR)

    # 2. Waiting charges
    billable_wait = max(0.0, float(wait_time_min) - WAIT_FREE_MIN)
    wait_charge   = billable_wait * WAIT_RATE

    # 3. Night surcharge
    night_adj = distance_fare * NIGHT_FACTOR if _is_night(hour) else 0.0

    # 4. Weather surge (multiplier above 1.0)
    weather_adj = distance_fare * max(0.0, float(weather_surge) - 1.0)

    # 5. Holiday (+8%)
    holiday_adj = distance_fare * 0.08 if is_holiday else 0.0

    # 6. Sub-total before GST
    subtotal = distance_fare + wait_charge + night_adj + weather_adj + holiday_adj
    if noise_pct > 0.0:
        subtotal *= 1.0 + random.uniform(-noise_pct, noise_pct)

    # 7. GST (5%) on full sub-total
    gst        = subtotal * GST_RATE
    final_fare = round(subtotal + gst, 2)

    return {
        "offered_fare":          final_fare,
        "base_fare_fixed":       round(BASE_FARE_FIXED, 2),
        "distance_fare":         round(distance_fare, 2),
        "wait_charge":           round(wait_charge, 2),
        "night_adj":             round(night_adj, 2),
        "weather_adj":           round(weather_adj, 2),
        "holiday_adj":           round(holiday_adj, 2),
        "gst_5_percent":         round(gst, 2),
        "subtotal_ex_gst":       round(subtotal, 2),
        "incremental_km":        round(incremental_km, 2),
        "rate_per_km_used":      rate_per_km,
        "is_night":              _is_night(hour),
        "is_ac":                 is_ac,
        "trip_type":             trip_type,
        "effective_rate_per_km": round(final_fare / km, 2) if km > 0 else 0.0,
    }

def predict_fare(sample: dict) -> dict:
    """Dict-in → fare breakdown dict-out. Accepts raw dataset rows or API payloads."""
    km        = float(sample.get("estimated_distance_km") or sample.get("actual_distance_km") or 0.0)
    is_ac     = str(sample.get("vehicle_type", "economy")).lower() == "premium"
    trip_type = str(sample.get("trip_type", "standard")).lower()
    hour      = int(sample["hour_of_day"]) if "hour_of_day" in sample else (18 if sample.get("is_peak_hour") else 12)
    wait      = float(sample.get("wait_time_min", 0.0))
    surge     = float(sample.get("weather_surge", 1.0))
    holiday   = bool(sample.get("is_holiday", False))
    return compute_fare(km=km, is_ac=is_ac, trip_type=trip_type, hour=hour,
                        wait_time_min=wait, weather_surge=surge, is_holiday=holiday)

if __name__ == "__main__":
    print("Urban Black Fare Engine — smoke test")
    cases = [
        (1.0,  False, 12, 0, 1.00, "1 km base"),
        (10.0, False, 12, 0, 1.00, "10 km short/med"),
        (15.0, False, 12, 0, 1.00, "15 km long-T1"),
        (18.0, False, 12, 0, 1.00, "18 km long-T2"),
        (20.0, False, 12, 0, 1.00, "20 km long-T3"),
        (25.0, False, 12, 0, 1.00, "25 km long-T3"),
        (16.0, True,  23, 8, 1.15, "16km AC+night+surge"),
        (52.0, False,  8, 0, 1.00, "52 km airport"),
    ]
    print(f"{'Label':<28} {'km':>5} {'Rate':>5} {'Fare':>8} {'₹/km':>8}")
    for km, ac, hr, wait, surge, label in cases:
        r = compute_fare(km, ac, "standard", hr, wait, surge)
        print(f"{label:<28} {km:>5.1f} ₹{r['rate_per_km_used']:>4}/km ₹{r['offered_fare']:>7.2f} ₹{r['effective_rate_per_km']:>7.2f}")
