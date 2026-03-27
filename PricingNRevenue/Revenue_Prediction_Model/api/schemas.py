from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float

    hour_of_day: int = Field(ge=0, le=23)

    driver_rating: float = Field(default=4.5, ge=1, le=5)
    driver_total_trips: int = 1000
    driver_shift_hours_elapsed: float = 6

    total_op_km_today: float = 80

    surge_multiplier: float = 1.0
    zone_surge_multiplier: float = 1.0

    number_of_rides_in_zone: int = 50
    number_of_active_drivers_in_zone: int = 20

    is_raining: bool = False
    waiting_time_min: int = 0