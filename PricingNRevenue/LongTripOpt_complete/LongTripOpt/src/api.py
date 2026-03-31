from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import sys
from pathlib import Path

# Add src to path if necessary
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.predict import predict_single

app = FastAPI(
    title="LongTripOpt Inference API",
    description="Real-time fare prediction and rider acceptance (WTA) for UrbanBlack long-distance rides.",
    version="1.0.0"
)

class RideRequest(BaseModel):
    estimated_distance_km: float
    vehicle_type: str = "economy"
    hour_of_day: int = 12
    trip_type: str = "standard_long"
    wait_time_min: float = 0.0
    weather_surge: float = 1.0
    is_holiday: bool = False
    driver_rating: Optional[float] = 4.5
    driver_total_trips: Optional[int] = 500
    driver_daily_ride_km: Optional[float] = 80
    driver_daily_dead_km: Optional[float] = 15

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "LongTripOpt",
        "version": "1.0.0"
    }

@app.post("/predict")
def get_prediction(request: RideRequest):
    """
    Predict fare (ML vs Rule) and Rider Acceptance (WTA) for a ride request.
    """
    try:
        sample = request.dict()
        result = predict_single(sample)
        # We can keep 'features' if the user wants to see the engineering, 
        # but usually cleaner to pop it.
        if "features" in result:
            result.pop("features")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
