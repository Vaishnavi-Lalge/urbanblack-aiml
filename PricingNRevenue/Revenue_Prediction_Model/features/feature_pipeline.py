import numpy as np
import joblib

# Load scaler
scaler = joblib.load("model/scaler.pkl")

def build_features(data):
    """
    Returns BOTH:
    - scaled features (for model)
    - raw features (for drift & explainability)
    """

    utilization = data.total_ride_km / data.total_km if data.total_km > 0 else 0

    weather_factor = getattr(data, "weather_factor", 1.0)
    traffic_factor = getattr(data, "traffic_factor", 1.0)
    surge = getattr(data, "surge", 1.0)

    raw_features = [
        data.driver_id,
        data.hour,
        data.day_of_week,
        data.rides_count,
        data.total_ride_km,
        data.total_km,
        data.dead_km,
        utilization,
        data.driver_rating,
        data.total_trips,
        data.shift_hours,
        weather_factor,
        traffic_factor,
        surge
    ]

    raw_array = np.array(raw_features).reshape(1, -1)
    scaled_array = scaler.transform(raw_array)

    return scaled_array, raw_features