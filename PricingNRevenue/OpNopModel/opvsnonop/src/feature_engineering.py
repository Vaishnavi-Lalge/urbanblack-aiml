import pandas as pd

TIME_SPLIT_COLUMN = "event_timestamp"


def _bucket_zone_number(zone_number: pd.Series) -> pd.Series:
    bins = [-1, 5, 10, 15, 99]
    labels = ["zone_01_05", "zone_06_10", "zone_11_15", "zone_16_plus"]
    bucket = pd.cut(zone_number, bins=bins, labels=labels)
    return bucket.astype("object").fillna("zone_unknown")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    start_ts = pd.to_datetime(data["segment_start_timestamp"], utc=True, errors="coerce")
    end_ts = pd.to_datetime(data["segment_end_timestamp"], utc=True, errors="coerce")

    data[TIME_SPLIT_COLUMN] = start_ts.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["start_weekday"] = start_ts.dt.dayofweek
    data["start_month"] = start_ts.dt.month
    data["is_weekend"] = start_ts.dt.dayofweek.isin([5, 6]).astype(int)
    data["day_part"] = pd.cut(
        start_ts.dt.hour.fillna(data["hour_of_day"]),
        bins=[-1, 5, 11, 16, 21, 24],
        labels=["overnight", "morning", "afternoon", "evening", "late_night"],
    ).astype("object")

    zone_parts = data["zone_id"].fillna("").astype(str).str.extract(
        r"^\s*(?P<zone_city_code>[^-]*?)(?:-(?P<zone_number>\d+))?\s*$"
    )
    zone_number = pd.to_numeric(zone_parts["zone_number"], errors="coerce")
    data["zone_city_code"] = zone_parts["zone_city_code"].replace("", "UNKNOWN").fillna("UNKNOWN")
    data["zone_bucket"] = _bucket_zone_number(zone_number)

    data["movement_activity"] = data["speed_kmh"] * data["ping_count"]
    data["idle_ratio"] = data["time_since_last_trip_end_min"] / (data["driver_shift_hours_elapsed"] + 1.0)
    data["segment_elapsed_min"] = (end_ts - start_ts).dt.total_seconds() / 60.0

    data = data.drop(columns=["segment_start_timestamp", "segment_end_timestamp", "zone_id"])
    return data
