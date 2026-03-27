"""
predict.py  —  LongTripOpt Inference Pipeline
=============================================
Loads trained fare + WTA models and runs inference on:
  • A single sample dict   (predict_single)
  • A CSV file             (predict_csv)
  • A quick CLI smoke-test (python src/predict.py)

Usage
-----
    # Single prediction from CLI
    python src/predict.py --km 18.5 --vehicle premium --hour 23 --trip-type airport --wait 7

    # Batch predict a CSV
    python src/predict.py --input-csv data/rides_dataset_clean.csv \
                          --output-csv data/predictions.csv
"""
from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import joblib
    def _load(path): return joblib.load(path)
except ImportError:
    import pickle
    def _load(path):
        with open(path, "rb") as f: return pickle.load(f)

warnings.filterwarnings("ignore")

ROOT       = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

# ─── lazy-load models once ────────────────────────────────────────────────────
_fare_model = None
_wta_model  = None
_feat_cols  = None

def _load_models():
    global _fare_model, _wta_model, _feat_cols
    if _fare_model is not None:
        return

    fare_path = MODELS_DIR / "fare_model.pkl"
    wta_path  = MODELS_DIR / "wta_model.pkl"
    feat_path = MODELS_DIR / "feature_columns.json"

    if not fare_path.exists():
        raise FileNotFoundError(
            f"Fare model not found at {fare_path}. "
            "Run `python src/train.py` first."
        )

    _fare_model = _load(fare_path)
    _wta_model  = _load(wta_path) if wta_path.exists() else None
    _feat_cols  = json.loads(feat_path.read_text()) if feat_path.exists() else {}


# ─── feature engineering (mirrors train.py — must stay in sync) ──────────────
TRIP_TYPE_ORDER = ["standard", "standard_long", "outskirts", "airport", "intercity"]
FUEL_ORDER      = ["LOW", "QUARTER", "HALF", "THREE_QUARTER", "FULL"]
COND_ORDER      = ["NEEDS_ATTENTION", "FAIR", "GOOD", "EXCELLENT"]

def _encode_ordinal(val: str, order: list[str]) -> int:
    mapping = {v: i for i, v in enumerate(order)}
    return mapping.get(str(val).lower() if val else "", 0)

def _fare_slab(km: float) -> int:
    if km < 15: return 1
    if km < 18: return 2
    if km < 20: return 3
    return 4

def _build_features(sample: dict) -> dict:
    """Transform a raw sample dict into the flat feature dict used by models."""
    km     = float(sample.get("estimated_distance_km") or sample.get("actual_distance_km") or 0)
    act_km = float(sample.get("actual_distance_km") or km)
    dur    = float(sample.get("actual_duration_min") or max(1, km * 2))
    est_dur= float(sample.get("estimated_duration_min") or dur)
    approach_km = float(sample.get("approach_km") or 2.0)
    hour   = int(sample.get("hour_of_day") or (18 if sample.get("is_peak_hour") else 12))
    dow    = int(sample.get("day_of_week") or 1)

    trip_type  = str(sample.get("trip_type", "standard")).lower().strip()
    veh_type   = str(sample.get("vehicle_type", "economy")).lower().strip()
    is_premium = int(veh_type == "premium")
    is_night   = int(hour >= 22 or hour < 6)

    hr_rad = hour * 2 * math.pi / 24
    dw_rad = dow  * 2 * math.pi / 7

    feats = {
        # distance
        "actual_distance_km":      act_km,
        "estimated_distance_km":   km,
        "distance_error_ratio":    max(-0.5, min(0.5, (km - act_km) / max(act_km, 0.1))),
        "actual_duration_min":     dur,
        "estimated_duration_min":  est_dur,
        "approach_km":             approach_km,
        "speed_kmh":               min(120, act_km / max(dur / 60, 0.01)),
        # trip classification
        "trip_type_enc":           _encode_ordinal(trip_type, TRIP_TYPE_ORDER),
        "vehicle_type_enc":        is_premium,
        "is_airport":              int(trip_type == "airport"),
        "is_intercity":            int(trip_type == "intercity"),
        "is_long_trip":            int(trip_type in ("standard_long","airport","intercity","outskirts")),
        "is_premium":              is_premium,
        # time
        "hour_of_day":             hour,
        "day_of_week":             dow,
        "is_peak_hour":            int(bool(sample.get("is_peak_hour", False))),
        "is_weekend":              int(bool(sample.get("is_weekend", False))),
        "is_night":                is_night,
        "hour_sin":                math.sin(hr_rad),
        "hour_cos":                math.cos(hr_rad),
        "dow_sin":                 math.sin(dw_rad),
        "dow_cos":                 math.cos(dw_rad),
        # fare slab
        "fare_slab_stage_id":      _fare_slab(km),
        # driver
        "driver_rating":               float(sample.get("driver_rating") or 4.5),
        "driver_total_trips":          int(sample.get("driver_total_trips") or 500),
        "driver_daily_ride_km":        float(sample.get("driver_daily_ride_km") or 80),
        "driver_daily_dead_km":        float(sample.get("driver_daily_dead_km") or 15),
        "driver_quota_km":             float(sample.get("driver_quota_km") or 135),
        "driver_overuse_km":           float(sample.get("driver_overuse_km") or 0),
        "driver_shift_hours_elapsed":  float(sample.get("driver_shift_hours_elapsed") or 4),
        "driver_online_minutes":       float(sample.get("driver_online_minutes") or 240),
        "driver_fuel_level_enc":       _encode_ordinal(
            sample.get("driver_fuel_level_start", "HALF"), FUEL_ORDER),
        "driver_vehicle_cond_enc":     _encode_ordinal(
            sample.get("driver_vehicle_condition", "GOOD"), COND_ORDER),
        # derived driver KPIs
        "shift_fatigue_score":         min(1.0, float(sample.get("driver_shift_hours_elapsed") or 4) / 12),
        "utilization_ratio":           float(sample.get("driver_daily_ride_km") or 80) / 135,
        "low_fuel_flag":               int(_encode_ordinal(
            sample.get("driver_fuel_level_start", "HALF"), FUEL_ORDER) <= 1),
        "poor_vehicle_flag":           int(_encode_ordinal(
            sample.get("driver_vehicle_condition", "GOOD"), COND_ORDER) == 0),
        "end_of_shift_flag":           int(float(sample.get("driver_shift_hours_elapsed") or 4) >= 10),
    }
    return feats


def _rule_fare(km: float, is_premium: bool, is_night: bool,
               wait_min: float = 0.0, surge: float = 1.0,
               is_holiday: bool = False) -> float:
    """Rule-based fare for comparison / fallback (mirrors fare_calculator.py)."""
    inc = max(0.0, km - 1.5)
    rate= 25 if km < 15 else (23 if km < 18 else (22 if km < 20 else 20))
    dist= (55 + inc * rate) * (1.10 if is_premium else 1.0)
    wait_charge = max(0.0, wait_min - 5) * 2
    night  = dist * 0.25 if is_night else 0
    weather= dist * max(0.0, surge - 1.0)
    holiday= dist * 0.08 if is_holiday else 0
    sub    = dist + wait_charge + night + weather + holiday
    return round(sub * 1.05, 2)


# ─── public API ──────────────────────────────────────────────────────────────

def predict_single(sample: dict) -> dict:
    """
    Predict fare and WTA for one ride request.

    Parameters
    ----------
    sample : dict  with ride fields (same schema as the dataset)

    Returns
    -------
    dict with keys:
        ml_fare          – model predicted fare (₹)
        rule_fare        – deterministic rule-based fare (₹)
        wta_probability  – probability rider accepts (0–1), if WTA model loaded
        wta_prediction   – 1 = will accept, 0 = will reject
        features         – feature vector used (for debugging)
    """
    _load_models()
    feats = _build_features(sample)
    feat_df = pd.DataFrame([feats])

    # Fare prediction
    fare_cols = _feat_cols.get("fare_features", list(feats.keys()))
    fare_cols = [c for c in fare_cols if c in feats]
    ml_fare   = round(float(_fare_model.predict(feat_df[fare_cols])[0]), 2)

    # Rule fare for reference
    km        = feats["estimated_distance_km"]
    rule_fare = _rule_fare(
        km        = km,
        is_premium= bool(feats["is_premium"]),
        is_night  = bool(feats["is_night"]),
        wait_min  = float(sample.get("wait_time_min", 0)),
        surge     = float(sample.get("weather_surge", 1.0)),
        is_holiday= bool(sample.get("is_holiday", False)),
    )

    # WTA prediction
    wta_prob = wta_pred = None
    if _wta_model is not None:
        wta_cols = _feat_cols.get("wta_features", list(feats.keys()))
        wta_cols = [c for c in wta_cols if c in feats]
        proba    = _wta_model.predict_proba(feat_df[wta_cols])[0]
        wta_prob = round(float(proba[1]), 4)
        wta_pred = int(wta_prob >= 0.5)

    return {
        "ml_fare":         ml_fare,
        "rule_fare":       rule_fare,
        "fare_diff_pct":   round((ml_fare - rule_fare) / max(rule_fare, 1) * 100, 2),
        "wta_probability": wta_prob,
        "wta_prediction":  wta_pred,
        "fare_slab":       _fare_slab(km),
        "is_long_trip":    bool(feats["is_long_trip"]),
        "features":        feats,
    }


def predict_csv(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Run inference on every row of a CSV and write predictions beside it."""
    _load_models()
    df  = pd.read_csv(input_path)
    print(f"Predicting {len(df):,} rows from {input_path} …")

    ml_fares, rule_fares, wta_probs, wta_preds, slabs = [], [], [], [], []

    fare_cols = _feat_cols.get("fare_features", [])
    wta_cols  = _feat_cols.get("wta_features", [])

    feat_rows = [_build_features(row.to_dict()) for _, row in df.iterrows()]
    feat_df   = pd.DataFrame(feat_rows)

    # Batch fare prediction
    fc = [c for c in fare_cols if c in feat_df.columns]
    ml_fares = [round(v, 2) for v in _fare_model.predict(feat_df[fc])]

    # Batch rule fare
    for feat in feat_rows:
        rule_fares.append(_rule_fare(
            km=feat["estimated_distance_km"],
            is_premium=bool(feat["is_premium"]),
            is_night=bool(feat["is_night"]),
        ))
        slabs.append(_fare_slab(feat["estimated_distance_km"]))

    # Batch WTA
    if _wta_model is not None:
        wc = [c for c in wta_cols if c in feat_df.columns]
        proba = _wta_model.predict_proba(feat_df[wc])[:, 1]
        wta_probs = [round(float(p), 4) for p in proba]
        wta_preds = [int(p >= 0.5) for p in proba]
    else:
        wta_probs = [None] * len(df)
        wta_preds = [None] * len(df)

    df["pred_fare_ml"]       = ml_fares
    df["pred_fare_rule"]     = rule_fares
    df["pred_fare_diff_pct"] = [round((m - r) / max(r, 1) * 100, 2)
                                 for m, r in zip(ml_fares, rule_fares)]
    df["pred_wta_prob"]      = wta_probs
    df["pred_wta"]           = wta_preds
    df["pred_fare_slab"]     = slabs

    df.to_csv(output_path, index=False)
    print(f"✅  Predictions written to {output_path}")
    return df


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="LongTripOpt — Inference")
    p.add_argument("--km",        type=float, default=20.0,  help="Trip distance in km")
    p.add_argument("--vehicle",   default="economy",          help="economy | premium")
    p.add_argument("--hour",      type=int,   default=12,     help="Hour of day (0-23)")
    p.add_argument("--trip-type", default="standard_long",    help="Trip type")
    p.add_argument("--wait",      type=float, default=0.0,    help="Wait time in minutes")
    p.add_argument("--surge",     type=float, default=1.0,    help="Weather surge multiplier")
    p.add_argument("--input-csv", default=None,               help="Batch: input CSV path")
    p.add_argument("--output-csv",default=None,               help="Batch: output CSV path")
    args = p.parse_args()

    if args.input_csv:
        out = args.output_csv or str(ROOT / "data" / "predictions.csv")
        predict_csv(Path(args.input_csv), Path(out))
        return

    # Single prediction
    sample = {
        "estimated_distance_km": args.km,
        "vehicle_type":          args.vehicle,
        "hour_of_day":           args.hour,
        "trip_type":             args.trip_type,
        "wait_time_min":         args.wait,
        "weather_surge":         args.surge,
    }

    result = predict_single(sample)
    print("\n" + "=" * 55)
    print(f"  Trip   : {args.km} km | {args.vehicle} | {args.trip_type}")
    print(f"  Time   : hour={args.hour} | wait={args.wait} min | surge={args.surge}x")
    print(f"  Slab   : {result['fare_slab']} | Long trip: {result['is_long_trip']}")
    print("-" * 55)
    print(f"  ML Fare   : ₹{result['ml_fare']:.2f}")
    print(f"  Rule Fare : ₹{result['rule_fare']:.2f}  (diff {result['fare_diff_pct']:+.1f}%)")
    if result["wta_probability"] is not None:
        accept = "✅ ACCEPT" if result["wta_prediction"] else "❌ REJECT"
        print(f"  WTA       : {accept}  (p={result['wta_probability']:.3f})")
    print("=" * 55)

    # Quick sanity-check table
    print("\nFare slab reference:")
    for km, label in [(10,"short/med"), (15,"long-T1"), (18,"long-T2"), (20,"long-T3"), (25,"long-T3")]:
        s = predict_single({"estimated_distance_km": km, "hour_of_day": 12,
                             "vehicle_type": "economy", "trip_type": "standard_long"})
        print(f"  {km:>3} km ({label:<12}): rule ₹{s['rule_fare']:.2f}  ml ₹{s['ml_fare']:.2f}")


if __name__ == "__main__":
    main()
