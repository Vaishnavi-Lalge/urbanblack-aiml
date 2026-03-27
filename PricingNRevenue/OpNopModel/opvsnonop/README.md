# Operational vs Non-Operational KM Classifier

This project predicts whether a mobility segment is `Operational` or `Non-Operational` using a hybrid decision system:

- XGBoost classifier
- isotonic probability calibration
- time-based train/calibration/test split
- lightweight rule overrides for business edge cases
- FastAPI inference service

## Current pipeline

1. Raw data is read from `data/OPERATIONAL VS NON-OPERATIONAL KM CLASSIFIER.csv`
2. `src/preprocess.py` cleans the raw dataset and writes `data/clean_data.csv`
3. `src/train.py` trains the calibrated model and saves `models/model.pkl`
4. `src/evaluate_system.py` evaluates the full hybrid system
5. `src/api.py` serves predictions through FastAPI

## Project structure

- `data/OPERATIONAL VS NON-OPERATIONAL KM CLASSIFIER.csv`: raw labeled dataset
- `data/clean_data.csv`: cleaned dataset used for training and evaluation
- `src/preprocess.py`: preprocessing and feature engineering entrypoint
- `src/feature_engineering.py`: derived feature creation
- `src/train.py`: model training, calibration, and hybrid decision config selection
- `src/decision_logic.py`: hybrid decision rules and score adjustment logic
- `src/evaluate_system.py`: offline evaluation script for the full system
- `src/api.py`: prediction API
- `models/model.pkl`: saved calibrated model artifact and decision config

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run preprocessing

```powershell
.\.venv\Scripts\python src\preprocess.py
```

## Train the model

```powershell
.\.venv\Scripts\python src\train.py
```

## Evaluate the hybrid system

```powershell
.\.venv\Scripts\python src\evaluate_system.py
```

## Run the API

```powershell
.\.venv\Scripts\python -m uvicorn src.api:app --reload
```

## API request fields

The API expects raw segment fields. Feature engineering is applied internally before scoring.

Required request fields:

- `city`
- `segment_start_timestamp`
- `segment_end_timestamp`
- `latitude`
- `longitude`
- `speed_kmh`
- `heading_degrees`
- `gps_accuracy_meters`
- `total_distance_km`
- `avg_speed_kmh`
- `max_speed_kmh`
- `speed_std_dev`
- `heading_variance`
- `ping_count`
- `duration_seconds`
- `is_near_accepted_pickup`
- `road_speed_limit_kmh`
- `speed_vs_road_limit_ratio`
- `zone_id`
- `hour_of_day`
- `driver_shift_hours_elapsed`
- `time_since_last_trip_end_min`
- `consecutive_operational_segments_count`

## API response

The prediction response includes:

- `prediction`
- `label`
- `confidence`
- `decision_score`
- `source`
- `source_type`
- `reason`
- `adjustments`
- `total_adjustment`