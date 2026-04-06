from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    # ===== LOCATION =====
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float

    # ===== TEMPORAL =====
    hour_of_day: int = Field(ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(default=0, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    is_holiday: bool = Field(default=False, description="Is today a holiday?")

    # ===== DRIVER INFO =====
    driver_rating: float = Field(default=4.5, ge=1, le=5, description="Driver rating 1-5 stars")
    driver_total_trips: int = Field(default=1000, ge=0, description="Total lifetime trips")
    driver_shift_hours_elapsed: float = Field(default=6, ge=0, description="Hours worked today")
    rides_completed_so_far: int = Field(default=5, ge=0, description="Rides completed today")
    is_female_driver: bool = Field(default=False, description="Is driver female? (for inclusivity bonus)")
    
    # ===== TRIP INFO =====
    total_op_km_today: float = Field(default=80, ge=0, description="KMs driver has done today")
    waiting_time_min: int = Field(default=0, ge=0, description="Pickup wait time in minutes")
    
    # ===== DEMAND & SUPPLY =====
    surge_multiplier: float = Field(default=1.0, ge=0.5, le=5.0, description="Uber surge multiplier")
    zone_surge_multiplier: float = Field(default=1.0, ge=0.5, le=5.0, description="Zone-specific surge")
    number_of_rides_in_zone: int = Field(default=50, ge=0, description="Active ride requests in zone")
    number_of_active_drivers_in_zone: int = Field(default=20, ge=1, description="Active drivers in zone")
    
    # ===== ENVIRONMENT =====
    is_raining: bool = Field(default=False, description="Is it raining?")
    weather_type: str = Field(
        default="clear",
        description="Weather type: 'clear', 'cloudy', 'light_rain', 'heavy_rain', 'fog'"
    )


class PredictionResponse(BaseModel):
    """Response schema for prediction endpoint."""
    prediction_status: str
    predicted_revenue: float = Field(description="Predicted earnings in INR")
    predicted_rides: int = Field(description="Predicted number of rides")
    earnings_range: str = Field(description="Earnings range e.g. '₹250 - ₹350'")
    rides_range: str = Field(description="Rides range e.g. '8 - 12 rides'")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence 0-1")
    confidence_breakdown: dict = Field(description="Breakdown of confidence components")
    revenue_breakdown: dict = Field(description="Breakdown of revenue calculation")
    rides_breakdown: dict = Field(description="Breakdown of rides calculation")
    explainability: list = Field(description="Top features influencing prediction")
    alerts: list = Field(default_factory=list, description="Any alerts or warnings")