from src.fare_calculator import predict_fare

sample_base = {
    'actual_distance_km': 16.0,
    'estimated_distance_km': 16.0,
    'approach_km': 2.0,
    'actual_duration_min': 35,
    'estimated_duration_min': 33,
    'trip_type': 'standard',
    'is_peak_hour': True,
    'wait_time_min': 8.0,      # 8 mins wait -> 3 mins billable (first 5 free)
    'weather_surge': 1.15,     # 15% weather surge
    'hour_of_day': 23          # 11 PM -> triggers night charge (25%)
}

if __name__ == "__main__":
    print(f"--- Fares for {sample_base['estimated_distance_km']}km ({sample_base['trip_type']}) ---")
    
    # Calculate for Economy
    sample_eco = {**sample_base, 'vehicle_type': 'economy'}
    res_eco = predict_fare(sample_eco)
    print(f"Economy Fare: Rs {res_eco['offered_fare']:.2f}")

    # Calculate for Premium
    sample_prem = {**sample_base, 'vehicle_type': 'premium'}
    res_prem = predict_fare(sample_prem)
    print(f"Premium Fare: Rs {res_prem['offered_fare']:.2f}")

    print("\nDetailed Breakdown (Economy):")
    for k, v in res_eco.items():
        if k != 'offered_fare':
            print(f"  {k}: {v}")
