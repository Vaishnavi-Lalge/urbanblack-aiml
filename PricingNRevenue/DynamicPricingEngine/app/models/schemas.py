from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PricingRequest(BaseModel):
    request_id: str = Field(..., description="Unique booking request identifier")
    timestamp: datetime = Field(..., description="Timestamp of the request")
    pickup_lat: float
    pickup_lon: float
    dropoff_lat: float
    dropoff_lon: float
    estimated_distance_km: float
    estimated_duration_min: int
    vehicle_category: str = Field(..., description="economy, premium, xl, auto")
    toll_cost_estimate: float = 0.0
    hour_of_day: int
    is_peak_hour: bool
    is_holiday: bool
    is_night_trip: bool = False
    waiting_time_minutes: int = 0
    zone_demand_supply_ratio: float
    rainfall_mm_per_hour: float = 0.0
    active_event_in_zone: bool = False
    available_drivers_in_zone: int


class FareBreakdown(BaseModel):
    base_fare: float
    distance_charge: float
    waiting_charge: float
    night_surcharge: float
    weather_surcharge: float
    demand_surge_amount: float
    toll_component: float
    platform_fee: float
    gst_amount: float

class PricingResponse(BaseModel):
    estimated_computed_fare: float
    currency: str = "INR"
