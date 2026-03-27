from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd

app    = FastAPI(title="KM Classifier API - Urban Black Taxi")
model  = joblib.load("../models/km_classifier.pkl")
scaler = joblib.load("../models/scaler.pkl")

class RideInput(BaseModel):
    status: int
    driver_availability: int
    demand_level: int
    fare_INR: float
    rideKm: float
    durationMin: float
    pickup_lat: float
    pickup_lng: float
    drop_lat: float
    drop_lng: float
    peak_hour_flag: int
    demand_supply_ratio: float
    surge_multiplier: float
    hour: int
    day_of_week: int
    month: int

@app.get("/health")
def health():
    return {"status": "ok", "model": "KM Classifier"}

@app.post("/classify")
def classify(ride: RideInput):
    input_df = pd.DataFrame([ride.dict()])
    scaled   = scaler.transform(input_df)
    pred     = model.predict(scaled)[0]
    label    = "Operational" if pred == 1 else "Non-Operational"
    return {
        "prediction": int(pred),
        "label": label,
        "message": "Real-time processing" if pred == 1 else "Analytical processing"
    }