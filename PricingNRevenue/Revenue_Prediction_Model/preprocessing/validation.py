def validate_data(df):

    required_cols = [
        "trip_distance",
        "trip_duration_min",
        "fare_amount",
        "driver_rating"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    print("✅ Data validated")

    return df