# ▣ Driver Revenue & Ride Prediction Service  
## Version: 1.0 (Production Ready – Real Dataset)

---

## ▣ Overview

The **Driver Revenue & Ride Prediction Service** is a production-grade Machine Learning system designed for ride-hailing platforms (UrbanBlack, Uber, Ola type systems).

It provides:

- Real-time driver revenue prediction
- Ride count estimation
- Business rule-based pricing adjustments
- Explainability using SHAP
- Drift detection for data validation
- Monitoring and logging
- Automated daily retraining pipeline

---

## ▣ Key Features

- Real-world pricing logic (₹55 base + ₹25/km)
- Bonus logic (₹12/km after 135 km)
- Night and weather surge handling
- Google Maps integration (distance + duration)
- Fully automated ML pipeline
- IST timezone consistency (Asia/Kolkata)

---

## ▣ Architecture

```

Client (Backend / Mobile App)
│
▼
FastAPI Service (/predict)
│
├── Maps Service (Distance & Duration)
├── Feature Pipeline
├── ML Models (Revenue + Rides)
├── Pricing Engine (Business Rules)
├── Explainability (SHAP)
├── Drift Detection
└── Monitoring Layer
│
▼
JSON Response

````

---

## ▣ Tech Stack

- Python 3.11+
- FastAPI
- Scikit-learn
- XGBoost
- SHAP
- Uvicorn
- Google Maps API
- Schedule (automation)

---

## ▣ Installation

### Clone Repository
```bash
git clone <repo_url>
cd Revenue_Prediction_Model
````

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▣ Running the System

### Run API Server

```bash
uvicorn api.app:app --reload
```

Access API Docs:

```
http://127.0.0.1:8000/docs
```

---

## ▣ Commands (Operational Guide)

### Run Full ML Pipeline (Manual)

```bash
python -m pipelines.daily_pipeline
```

---

### Start Auto Retraining Scheduler

```bash
python -m training.retrain_scheduler
```

Runs daily at **02:00 AM IST**

---

### Run Only Preprocessing

```bash
python -m preprocessing.run_preprocess
```

---

### Run Only Training

```bash
python -m training.train
```

---

### Test API

```bash
python tests/test_api.py
```

---

## ▣ Pipeline Modes

### Manual Mode

```bash
python -m pipelines.daily_pipeline
```

---

### Automated Mode

```bash
python -m training.retrain_scheduler
```

* Executes daily at 02:00 AM IST
* Automatically updates models

---

### Real-Time Mode

```bash
uvicorn api.app:app --reload
```

* Uses latest trained models
* No retraining during inference

---

## ▣ API Endpoint

### POST `/predict`

### Request Example

```json
{
  "pickup_lat": 18.5204,
  "pickup_lng": 73.8567,
  "drop_lat": 18.7041,
  "drop_lng": 73.7997,
  "hour_of_day": 18,
  "driver_rating": 4.7,
  "driver_total_trips": 1200,
  "driver_shift_hours_elapsed": 6,
  "total_op_km_today": 90,
  "surge_multiplier": 1.3,
  "zone_surge_multiplier": 1.2,
  "number_of_rides_in_zone": 80,
  "number_of_active_drivers_in_zone": 25,
  "is_raining": false,
  "waiting_time_min": 5
}
```

---

### Response Example

```json
{
  "prediction_status": "success",
  "predicted_revenue": 1034.21,
  "predicted_rides": 12,
  "earnings_range": "₹930.79 - ₹1137.63",
  "rides_range": "11 - 13 rides",
  "confidence": 0.64,
  "explainability": [...],
  "drift": {...}
}
```

---

## ▣ Prediction Logic

### Revenue Calculation

* ML model predicts base revenue
* Adjusted using:

  * Base fare (₹55)
  * ₹25 per km
  * Surge multiplier
  * Night charge (+25%)
  * Weather surge (10–20%)
  * Waiting charges
  * Bonus (₹12/km beyond 135 km)

---

### Ride Prediction

* ML-based prediction
* Aligned with:

  * 25 min per ride
  * 12-hour shift logic

---

## ▣ Explainability

Uses SHAP values to identify feature impact:

* trip_distance
* surge_multiplier
* demand_supply_ratio
* driver_rating

---

## ▣ Drift Detection

* Z-score based validation
* Detects out-of-distribution inputs

---

## ▣ Monitoring

Logs every prediction:

* Input data
* Output prediction
* Timestamp (IST)

### Metrics tracked:

* Total predictions
* Average revenue
* Drift occurrences

---

## ▣ Folder Structure

```
api/
features/
model/
monitoring/
preprocessing/
training/
services/
explainability/
utils/
data/
```

---

## ▣ Timezone

All timestamps follow:

```
Asia/Kolkata (IST)
```

---

## ▣ Production Notes

* Replace JSON logs with database (PostgreSQL / Kafka)
* Add authentication (JWT)
* Add model versioning
* Deploy using Docker
* Use CI/CD pipelines

---

## ▣ Maintainer

AI/ML Engineer – Driver Revenue Prediction System

```

