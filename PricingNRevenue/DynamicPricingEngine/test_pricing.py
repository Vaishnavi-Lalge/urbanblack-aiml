import asyncio
from datetime import datetime, timezone
from app.models.schemas import PricingRequest
from app.services.pricing_calculator import PricingCalculator

async def run_test():
    req = PricingRequest(
        request_id="test_req_123_new_rules",
        timestamp=datetime.now(timezone.utc),
        pickup_lat=19.0, pickup_lon=72.0,
        dropoff_lat=19.1, dropoff_lon=72.1,
        estimated_distance_km=15.0,
        estimated_duration_min=30,
        vehicle_category="economy",
        toll_cost_estimate=20.0,
        hour_of_day=23, # Night trip
        is_peak_hour=True,
        is_holiday=False,
        is_night_trip=True,
        waiting_time_minutes=10, # 5 min chargeable
        zone_demand_supply_ratio=2.6,
        rainfall_mm_per_hour=12.0, # Heavy rain
        active_event_in_zone=False,
        available_drivers_in_zone=5
    )
    
    calc = PricingCalculator()
    resp = await calc.calculate(req)
    
    print("--- Pricing Engine Response (NEW RULES) ---")
    print(f"Request ID: {resp.request_id}")
    print(f"Multiplier: {resp.surge_multiplier}x")
    print(f"Surge Tier: {resp.surge_tier}")
    print(f"Final Fare: {resp.final_fare} {resp.currency}")
    import json
    print(f"Breakdown: {json.dumps(resp.fare_breakdown.dict(), indent=2)}")
    
if __name__ == "__main__":
    asyncio.run(run_test())
