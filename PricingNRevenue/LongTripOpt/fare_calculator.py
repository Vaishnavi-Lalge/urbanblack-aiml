"""
src/utils/fare_calculator.py
Urban Black REAL fare calculator — derived from 80-row production dataset.

Two-tier system:
  SHORT trips (≤21 km): stage_patti ₹31/slab (screenshot-verified)
  LONG trips  (>30 km): discounted trip-type rates (empirically derived)

Long-trip slab rates (₹ per 1.5 km slab), verified from real data:
  ┌──────────────────┬─────────┬──────────┬──────────┐
  │ Trip type        │ economy │ premium  │ peak mult│
  ├──────────────────┼─────────┼──────────┼──────────┤
  │ standard_long    │  17.72  │  22.27   │   1.198  │
  │ outskirts        │  18.12  │  22.23   │   1.198  │
  │ airport          │  26.94  │  33.41   │   1.204  │
  │ intercity        │  27.50  │  33.71   │   1.198  │
  └──────────────────┴─────────┴──────────┴──────────┘
"""
import math, yaml, random
from pathlib import Path

_CFG  = yaml.safe_load(open(Path(__file__).parents[2] / "config" / "config.yaml"))
_F    = _CFG["fare"]
PEAK_HRS = set(_F["peak_hours"])

# Short-trip slab (stage_patti — screenshot verified)
SHORT_SLAB_RATE = 31.0
SHORT_AC_MULT   = 1.10
SLAB_KM         = 1.5

# Long-trip slab rates (₹/slab) — from real production data
LONG_RATES = {
    ("standard_long", "economy"): 17.72,
    ("standard_long", "premium"): 22.27,
    ("outskirts",     "economy"): 18.12,
    ("outskirts",     "premium"): 22.23,
    ("airport",       "economy"): 26.94,
    ("airport",       "premium"): 33.41,
    ("intercity",     "economy"): 22.34,
    ("intercity",     "premium"): 28.14,
}
PEAK_MULT    = 1.198   # +19.8% peak (07-10, 17-21)
NIGHT_MULT   = 1.05    # +5%  night  (22-06)
HOLIDAY_MULT = 1.08    # +8%  holiday


def _slabs(km: float) -> int:
    return math.ceil(km / SLAB_KM)


def compute_fare(km: float, is_ac: bool, trip_type: str,
                 hour: int, is_holiday: bool = False,
                 noise_pct: float = 0.0) -> dict:
    """
    Compute long-trip fare using the real Urban Black rate structure.
    Returns full breakdown dict.
    """
    vtype    = "premium" if is_ac else "economy"
    n_slabs  = _slabs(km)
    base_rate= LONG_RATES.get((trip_type, vtype),
                               LONG_RATES[("standard_long", vtype)])
    base_fare= round(n_slabs * base_rate, 2)

    is_peak  = hour in PEAK_HRS
    is_night = hour >= 22 or hour < 6

    peak_adj    = round(base_fare * (PEAK_MULT - 1),   2) if is_peak    else 0.0
    night_adj   = round(base_fare * (NIGHT_MULT - 1),  2) if is_night   else 0.0
    holiday_adj = round(base_fare * (HOLIDAY_MULT - 1),2) if is_holiday else 0.0

    sub = base_fare + peak_adj + night_adj + holiday_adj
    if noise_pct > 0:
        sub *= (1 + random.uniform(-noise_pct, noise_pct))

    min_f      = 31.0
    offered    = round(max(min_f, sub), 2)
    slab_id    = _slab_id(km)

    return {
        "offered_fare": offered,
        "base_fare":    base_fare,
        "peak_adj":     peak_adj,
        "night_adj":    night_adj,
        "holiday_adj":  holiday_adj,
        "is_peak":      is_peak,
        "slab_id":      slab_id,
        "n_slabs":      n_slabs,
        "per_km":       round(offered / km, 2) if km > 0 else 0,
        "slab_rate":    base_rate,
    }


def _slab_id(km: float) -> int:
    bands = [(0,1.5,1),(1.5,3,2),(3,4.5,3),(4.5,6,4),(6,7.5,5),
             (7.5,9,6),(9,10.5,7),(10.5,12,8),(12,13.5,9),(13.5,15,10),
             (15,16.5,11),(16.5,18,12),(18,19.5,13),(19.5,21,14),
             (21,30,15),(30,45,16),(45,60,17),(60,80,18),(80,9999,19)]
    for lo, hi, sid in bands:
        if lo <= km < hi:
            return sid
    return 19


def validate_against_real(csv_path="/tmp/real_dataset_clean.csv"):
    """
    Validate the fare formula against the real 80-row dataset.
    Prints MAE per trip type and overall.
    """
    import pandas as pd, numpy as np
    df  = pd.read_csv(csv_path)
    c   = df[df["ride_status"] == "RIDE_COMPLETED"].copy()
    preds = []
    for _, r in c.iterrows():
        res = compute_fare(
            r["actual_distance_km"],
            r["vehicle_type"] == "premium",
            r["trip_type"], int(r["hour_of_day"]),
            False, noise_pct=0.0
        )
        preds.append(res["offered_fare"])
    c["predicted"] = preds
    c["err"]       = abs(c["offered_fare"] - c["predicted"])
    print("── Fare Formula Validation vs Real Data ──────────────────")
    for tt, g in c.groupby("trip_type"):
        print(f"  {tt:<15} n={len(g):>2}  "
              f"actual=₹{g['offered_fare'].mean():.0f}  "
              f"pred=₹{g['predicted'].mean():.0f}  "
              f"MAE=₹{g['err'].mean():.1f}")
    print(f"  {'OVERALL':<15} n={len(c):>2}  MAE=₹{c['err'].mean():.1f}")
    return c["err"].mean()


if __name__ == "__main__":
    try:
        mae = validate_against_real()
        print(f"\nFormula MAE on real data: ₹{mae:.2f}")
    except FileNotFoundError:
        print("Real dataset not found, skipping validation.")
    print("\nSample long-trip fares:")
    for km, tt, ac, h in [(32,"standard_long",False,8),(45,"airport",True,18),
                           (75,"intercity",False,9),(50,"outskirts",True,17)]:
        r = compute_fare(km, ac, tt, h)
        print(f"  {km:>4}km {tt:<14} {'AC' if ac else 'Non-AC':<7} "
              f"h={h:>2}  ₹{r['offered_fare']:.0f}  "
              f"({r['per_km']:.2f}/km)")
