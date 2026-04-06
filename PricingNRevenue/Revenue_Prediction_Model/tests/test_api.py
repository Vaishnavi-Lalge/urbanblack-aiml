import requests
import json


URL = "http://127.0.0.1:8000/predict"


def validate_response(data, test_name):
    """Validate response structure and values."""
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

    assert data["prediction_status"] == "success", "❌ Prediction failed"
    assert data["predicted_revenue"] > 0, "❌ Revenue should be positive"
    assert data["predicted_rides"] >= 1, "❌ Rides should be >= 1"
    assert 0 <= data["confidence"] <= 1, "❌ Invalid confidence score"
    assert isinstance(data["explainability"], list), "❌ Explainability not list"
    assert len(data["explainability"]) > 0, "❌ Empty explainability"
    assert isinstance(data["drift"], dict), "❌ Drift not dict"

    print(f"\n✅ {test_name} PASSED")
    print(f"   Revenue: ₹{data['predicted_revenue']:.2f}")
    print(f"   Rides: {data['predicted_rides']}")
    print(f"   Confidence: {data['confidence']:.2%}")
    print(f"   Range: {data['earnings_range']}")


def test_evening_peak():
    """Test 1: Evening Peak Hours (High Demand)."""
    print("\n" + "="*70)
    print("TEST 1: EVENING PEAK HOURS (6 PM - HIGH DEMAND)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5314,
        "drop_lng": 73.8446,
        "hour_of_day": 18,  # 6 PM
        "driver_rating": 4.7,
        "driver_total_trips": 1200,
        "driver_shift_hours_elapsed": 6,
        "total_op_km_today": 90,
        "surge_multiplier": 1.3,
        "zone_surge_multiplier": 1.2,
        "number_of_rides_in_zone": 80,  # High rides
        "number_of_active_drivers_in_zone": 25,  # Low drivers
        "is_raining": False,
        "waiting_time_min": 5
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Evening Peak")
    return data


def test_night_surge():
    """Test 2: Late Night with High Surge."""
    print("\n" + "="*70)
    print("TEST 2: LATE NIGHT WITH HIGH SURGE (2 AM)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5314,
        "drop_lng": 73.8446,
        "hour_of_day": 2,  # 2 AM (night)
        "driver_rating": 4.5,
        "driver_total_trips": 800,
        "driver_shift_hours_elapsed": 8,
        "total_op_km_today": 120,
        "surge_multiplier": 2.5,  # HIGH SURGE!
        "zone_surge_multiplier": 1.5,
        "number_of_rides_in_zone": 150,  # Extremely high demand
        "number_of_active_drivers_in_zone": 10,  # Very few drivers
        "is_raining": False,
        "waiting_time_min": 10
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Late Night Surge")
    return data


def test_rainy_conditions():
    """Test 3: Rainy Weather Impact."""
    print("\n" + "="*70)
    print("TEST 3: RAINY WEATHER (WEATHER SURGE)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.6315,  # Longer distance
        "drop_lng": 73.9015,
        "hour_of_day": 15,  # 3 PM
        "driver_rating": 4.2,
        "driver_total_trips": 500,
        "driver_shift_hours_elapsed": 4,
        "total_op_km_today": 45,
        "surge_multiplier": 1.8,  # Rain causes higher surge
        "zone_surge_multiplier": 1.3,
        "number_of_rides_in_zone": 100,
        "number_of_active_drivers_in_zone": 20,
        "is_raining": True,  # RAINING!
        "waiting_time_min": 8
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Rainy Conditions")
    return data


def test_morning_rush():
    """Test 4: Morning Rush Hour."""
    print("\n" + "="*70)
    print("TEST 4: MORNING RUSH HOUR (8 AM)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.4950,
        "drop_lng": 73.8150,
        "hour_of_day": 8,  # 8 AM
        "driver_rating": 4.9,  # Excellent driver
        "driver_total_trips": 2500,
        "driver_shift_hours_elapsed": 2,
        "total_op_km_today": 30,
        "surge_multiplier": 1.4,
        "zone_surge_multiplier": 1.1,
        "number_of_rides_in_zone": 120,
        "number_of_active_drivers_in_zone": 40,
        "is_raining": False,
        "waiting_time_min": 3
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Morning Rush")
    return data


def test_off_peak_low_demand():
    """Test 5: Off-Peak Low Demand."""
    print("\n" + "="*70)
    print("TEST 5: OFF-PEAK LOW DEMAND (11 AM - NO SURGE)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5400,
        "drop_lng": 73.8600,
        "hour_of_day": 11,  # 11 AM (off-peak)
        "driver_rating": 3.8,  # Average driver
        "driver_total_trips": 400,
        "driver_shift_hours_elapsed": 5,
        "total_op_km_today": 60,
        "surge_multiplier": 1.0,  # NO SURGE
        "zone_surge_multiplier": 1.0,
        "number_of_rides_in_zone": 20,  # Low demand
        "number_of_active_drivers_in_zone": 60,  # Many drivers
        "is_raining": False,
        "waiting_time_min": 2
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Off-Peak Low Demand")
    return data


def test_long_distance_trip():
    """Test 6: Long Distance Trip (Highway)."""
    print("\n" + "="*70)
    print("TEST 6: LONG DISTANCE HIGHWAY TRIP (30+ KM)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 19.0854,  # 30+ km away
        "drop_lng": 73.1734,
        "hour_of_day": 14,  # 2 PM
        "driver_rating": 4.6,
        "driver_total_trips": 1500,
        "driver_shift_hours_elapsed": 3,
        "total_op_km_today": 50,
        "surge_multiplier": 1.1,
        "zone_surge_multiplier": 1.0,
        "number_of_rides_in_zone": 40,
        "number_of_active_drivers_in_zone": 35,
        "is_raining": False,
        "waiting_time_min": 4
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Long Distance Trip")
    return data


def test_short_distance_trip():
    """Test 7: Short Distance Trip (< 2 KM)."""
    print("\n" + "="*70)
    print("TEST 7: SHORT DISTANCE TRIP (< 2 KM)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5250,
        "drop_lng": 73.8600,
        "hour_of_day": 19,  # 7 PM
        "driver_rating": 4.3,
        "driver_total_trips": 900,
        "driver_shift_hours_elapsed": 7,
        "total_op_km_today": 100,
        "surge_multiplier": 1.2,
        "zone_surge_multiplier": 1.1,
        "number_of_rides_in_zone": 70,
        "number_of_active_drivers_in_zone": 28,
        "is_raining": False,
        "waiting_time_min": 6
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Short Distance Trip")
    return data


def test_low_rated_driver():
    """Test 8: Low-Rated Driver."""
    print("\n" + "="*70)
    print("TEST 8: LOW-RATED DRIVER (3.2 STARS)")
    print("="*70)
    
    payload = {
        "pickup_lat": 18.5204,
        "pickup_lng": 73.8567,
        "drop_lat": 18.5314,
        "drop_lng": 73.8446,
        "hour_of_day": 17,  # 5 PM
        "driver_rating": 3.2,  # LOW RATING!
        "driver_total_trips": 200,
        "driver_shift_hours_elapsed": 6,
        "total_op_km_today": 80,
        "surge_multiplier": 1.2,
        "zone_surge_multiplier": 1.0,
        "number_of_rides_in_zone": 50,
        "number_of_active_drivers_in_zone": 30,
        "is_raining": False,
        "waiting_time_min": 7
    }

    response = requests.post(URL, json=payload)
    assert response.status_code == 200, "❌ API not responding"
    data = response.json()
    validate_response(data, "Low-Rated Driver")
    return data


def run_all_tests():
    """Run all comprehensive tests."""
    print("\n" + "█"*70)
    print("█ COMPREHENSIVE API TEST SUITE - MULTIPLE SCENARIOS")
    print("█"*70)

    results = {
        "evening_peak": test_evening_peak(),
        "night_surge": test_night_surge(),
        "rainy_conditions": test_rainy_conditions(),
        "morning_rush": test_morning_rush(),
        "off_peak": test_off_peak_low_demand(),
        "long_distance": test_long_distance_trip(),
        "short_distance": test_short_distance_trip(),
        "low_rated_driver": test_low_rated_driver()
    }

    # Summary Comparison
    print("\n" + "█"*70)
    print("█ SUMMARY COMPARISON")
    print("█"*70 + "\n")
    print(f"{'Scenario':<20} {'Revenue':<15} {'Rides':<10} {'Confidence':<12}")
    print("-" * 60)
    
    for scenario, data in results.items():
        revenue = data["predicted_revenue"]
        rides = data["predicted_rides"]
        confidence = data["confidence"]
        print(f"{scenario:<20} ₹{revenue:<14.2f} {rides:<10} {confidence:<12.2%}")

    print("\n" + "█"*70)
    print("█ ✅ ALL TESTS PASSED SUCCESSFULLY!")
    print("█"*70 + "\n")

    return results


if __name__ == "__main__":
    run_all_tests()