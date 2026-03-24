# ▣ Revenue & Rides Prediction Service

## Overview

The Revenue & Rides Prediction Service is a production-ready Machine Learning API designed for driver-based mobility platforms (e.g., ride-hailing applications).  

It predicts:
- Expected driver revenue
- Expected number of rides
- Earnings and rides range (uncertainty handling)
- Confidence score
- Explainability (feature contribution using SHAP)
- Data drift (input validation against training distribution)

This service is built to integrate seamlessly with backend systems for real-time pricing and driver analytics.

---

## Architecture

```

Client (App / Backend)
│
▼
FastAPI Service (/predict)
│
├── Feature Engineering
├── Revenue Model (XGBoost)
├── Rides Model (XGBoost)
├── Explainability (SHAP)
├── Drift Detection
└── Monitoring Layer
│
▼
JSON Response

````

---

## Tech Stack

- Python 3.11+
- FastAPI (API layer)
- XGBoost (ML models)
- Scikit-learn (preprocessing, scaling)
- SHAP (explainability)
- Uvicorn (ASGI server)

---

## Installation

### 1. Clone Repository

```bash
git clone <repo_url>
cd <project_folder>
````

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run API Server

```bash
uvicorn api.app:app --reload
```

### 4. Access API Docs

```
http://127.0.0.1:8000/docs
```

---

## API Endpoint

### POST `/predict`

#### Request Format (application/json)

```json
{
  "driver_id": 15,
  "hour": 9,
  "day_of_week": 2,
  "rides_count": 5,
  "total_ride_km": 22,
  "total_km": 28,
  "ride_km": 22,
  "dead_km": 6,
  "driver_rating": 4.7,
  "total_trips": 1200,
  "shift_hours": 12,
  "weather_factor": 1.1,
  "traffic_factor": 0.9,
  "surge": 1.5
}
```

---

## Response Format

```json
{
  "prediction_status": "success",
  "predicted_revenue": 685.07,
  "predicted_rides": 5,
  "earnings_range": "₹616.56 - ₹753.58",
  "rides_range": "4 - 5 rides",
  "confidence": 0.81,
  "explainability": [
    {
      "feature": "total_ride_km",
      "impact": 210.63
    }
  ],
  "drift": {
    "hour": {
      "value": 9,
      "z_score": 0.36,
      "drift": false
    }
  }
}
```

---

## Field Definitions

### Input Fields

| Field          | Description                       |
| -------------- | --------------------------------- |
| driver_id      | Unique driver identifier          |
| hour           | Current hour (0–23)               |
| day_of_week    | Day index (0–6)                   |
| rides_count    | Completed rides in current window |
| total_ride_km  | Distance with passengers          |
| total_km       | Total distance traveled           |
| ride_km        | Passenger ride distance           |
| dead_km        | Distance without passengers       |
| driver_rating  | Driver rating (3.5–5.0)           |
| total_trips    | Historical trips count            |
| shift_hours    | Active working hours              |
| weather_factor | Weather impact multiplier         |
| traffic_factor | Traffic condition multiplier      |
| surge          | Dynamic pricing multiplier        |

---

### Output Fields

| Field             | Description                       |
| ----------------- | --------------------------------- |
| prediction_status | API execution status              |
| predicted_revenue | Estimated revenue                 |
| predicted_rides   | Estimated number of rides         |
| earnings_range    | Revenue range (uncertainty band)  |
| rides_range       | Ride count range                  |
| confidence        | Prediction confidence score       |
| explainability    | Feature-level contribution        |
| drift             | Input validation vs training data |

---

## Explainability

This service uses SHAP (SHapley Additive Explanations) to provide feature-level contributions for each prediction.

Example:

* total_ride_km → major contributor
* surge → pricing multiplier effect
* weather_factor → demand influence

This ensures transparency and interpretability of model outputs.

---

## Drift Detection

The system validates incoming inputs against training distribution using z-score.

* drift = false → safe prediction
* drift = true → out-of-distribution input

This helps maintain reliability in production environments.

---

## Integration Guide

### Backend Integration Flow

```
Backend Service
      │
      ▼
Send POST /predict (JSON)
      │
      ▼
Receive Prediction Response
      │
      ▼
Store / Display in Application
```

---

### Example (Python)

```python
import requests

url = "http://127.0.0.1:8000/predict"

data = {
    "driver_id": 15,
    "hour": 9,
    "day_of_week": 2,
    "rides_count": 5,
    "total_ride_km": 22,
    "total_km": 28,
    "ride_km": 22,
    "dead_km": 6,
    "driver_rating": 4.7,
    "total_trips": 1200,
    "shift_hours": 12,
    "weather_factor": 1.1,
    "traffic_factor": 0.9,
    "surge": 1.5
}

response = requests.post(url, json=data)
print(response.json())
```

---

## Monitoring

The service logs predictions internally and exposes metrics via:

### GET `/metrics`

Provides:

* Total predictions
* Average revenue
* Average rides
* Last prediction

---

## Production Considerations

* Replace in-memory logging with persistent storage (PostgreSQL / Kafka)
* Deploy using Docker + Kubernetes
* Add authentication (JWT / API Gateway)
* Enable model versioning
* Add CI/CD pipeline

---

## Folder Structure

```
api/
features/
model/
monitoring/
preprocessing/
training/
explainability/
utils/
data/
```

---

## Version

Current Version: **v6.0**

---

## Maintainer

AI/ML Developer – Revenue Prediction System

