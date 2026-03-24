from pydantic import BaseModel

class PredictionRequest(BaseModel):
    driver_id: int
    hour: int
    day_of_week: int
    rides_count: int
    total_ride_km: float
    total_km: float
    ride_km: float
    dead_km: float
    driver_rating: float
    total_trips: int
    shift_hours: float

    # 🔥 NEW FEATURES (match training)
    weather_factor: float = 1.0
    traffic_factor: float = 1.0
    surge: float = 1.0


class PredictionResponse(BaseModel):
    predicted_revenue: float
    predicted_rides: float
    confidence: float
    explainability: list
    drift: dict