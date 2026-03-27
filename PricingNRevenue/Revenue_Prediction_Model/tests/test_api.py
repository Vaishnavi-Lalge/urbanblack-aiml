import requests


URL = "http://127.0.0.1:8000/predict"


def test_prediction():
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5314,
        "drop_lng": 73.8446,
        "hour_of_day": 18,
        "driver_rating": 4.7,
        "driver_total_trips": 1200,
        "driver_shift_hours_elapsed": 6,
        "total_op_km_today": 90,
        "surge_multiplier": 1.3,
        "zone_surge_multiplier": 1.2,
        "number_of_rides_in_zone": 80,
        "number_of_active_drivers_in_zone": 25,
        "is_raining": False,
        "waiting_time_min": 5
    }

    response = requests.post(URL, json=payload)

    # ---------------- BASIC CHECK ----------------
    assert response.status_code == 200, "❌ API not responding"

    data = response.json()

    # ---------------- STRUCTURE CHECK ----------------
    required_keys = [
        "prediction_status",
        "predicted_revenue",
        "predicted_rides",
        "earnings_range",
        "rides_range",
        "confidence",
        "explainability",
        "drift"
    ]

    for key in required_keys:
        assert key in data, f"❌ Missing key: {key}"

    # ---------------- VALUE CHECK ----------------
    assert data["prediction_status"] == "success", "❌ Prediction failed"

    assert data["predicted_revenue"] > 0, "❌ Revenue should be positive"
    assert data["predicted_rides"] >= 1, "❌ Rides should be >= 1"

    assert 0 <= data["confidence"] <= 1, "❌ Invalid confidence score"

    # ---------------- EXPLAINABILITY CHECK ----------------
    assert isinstance(data["explainability"], list), "❌ Explainability not list"
    assert len(data["explainability"]) > 0, "❌ Empty explainability"

    # ---------------- DRIFT CHECK ----------------
    assert isinstance(data["drift"], dict), "❌ Drift not dict"

    print("\n✅ API TEST PASSED")
    print("📊 Response:")
    print(data)


if __name__ == "__main__":
    test_prediction()