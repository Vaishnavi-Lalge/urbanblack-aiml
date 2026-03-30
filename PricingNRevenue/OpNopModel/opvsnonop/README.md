# Operational vs Non-Operational Segment Classifier

This project classifies driver movement segments as `Operational` or `Non-Operational` using a hybrid ML system built for prediction, aggregation, and persistent driver-hour tracking.

## What the system does

- Trains an `XGBoost` classifier with `isotonic` probability calibration
- Uses a time-based split for train, calibration, and test evaluation
- Applies a small rule layer only for clear business edge cases
- Serves predictions through `FastAPI`
- Aggregates operational and non-operational time in `Xh Ym` format
- Stores processed segments and lifetime driver summaries in `SQLite`
- Prevents double counting through global `segment_id` deduplication
- Supports both single-driver and multi-driver batch aggregation

## Current model design

### ML layer

The saved model artifact in `models/model.pkl` contains:
- the calibrated sklearn pipeline
- the exact feature list used for inference
- the selected decision configuration for the hybrid layer

### Feature safety

The model is trained on cleaned and engineered features only.

Metadata columns are preserved for tracking but excluded from training:
- `segment_id`
- `driver_id`
- `duration_seconds`

This keeps the model safe from leakage while still allowing aggregation and lifetime analytics.

### Rule layer

The rule layer is intentionally minimal and only handles clear business edge cases:
- `rule_waiting_active`
- `rule_high_activity`

Normal cases are still handled by the calibrated model.

## Data files

- `data/OPERATIONAL VS NON-OPERATIONAL KM CLASSIFIER.csv`: raw labeled source dataset
- `data/clean_data.csv`: cleaned dataset used for training and evaluation
- `data/driver.db`: SQLite database created automatically for aggregation and lifetime storage

## Project structure

- `src/preprocess.py`: reads raw data, cleans it, preserves tracking metadata, writes `clean_data.csv`
- `src/feature_engineering.py`: shared feature engineering for training and inference
- `src/train.py`: trains the calibrated XGBoost pipeline and saves `models/model.pkl`
- `src/decision_logic.py`: hybrid decision logic and rule overrides
- `src/evaluate_system.py`: evaluates the full hybrid system offline
- `src/db.py`: SQLite tables and helper functions for dedup and summary updates
- `src/api.py`: FastAPI application for inference and aggregation
- `models/model.pkl`: trained model artifact

## Environment setup

Python `3.10+` is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the pipeline

### 1. Preprocess the raw dataset

```powershell
.\.venv\Scripts\python src\preprocess.py
```

### 2. Train the model

```powershell
.\.venv\Scripts\python src\train.py
```

### 3. Evaluate the hybrid system

```powershell
.\.venv\Scripts\python src\evaluate_system.py
```

### 4. Start the API

```powershell
.\.venv\Scripts\python -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

Swagger UI:
- `http://127.0.0.1:8000/docs`

## API endpoints

### `POST /predict`

Scores one segment and returns:
- `prediction`
- `label`
- `confidence`
- `decision_score`
- `source`
- `source_type`
- `reason`
- `hours`
- `adjustments`
- `total_adjustment`

### `POST /aggregate-hours`

Processes one or more segments, stores them in SQLite, updates lifetime driver totals, and returns:
- per-driver current batch hours
- per-driver lifetime hours
- processed and skipped segment counts
- per-segment status for processed, duplicate, or invalid segments

Important:
- each segment must include `segment_id` and `driver_id`
- `segment_id` is globally deduplicated in the database
- `duration_seconds <= 0` is skipped
- output hours are returned in `Xh Ym` format

## Aggregation behavior

The aggregation layer uses:
- `driver_segments` table for processed segment history
- `driver_summary` table for cumulative operational and non-operational seconds

This allows:
- idempotent reprocessing protection
- persistent lifetime tracking
- safe multi-driver batch ingestion

## Notes

- The API expects the full model input schema for every segment.
- The database file `data/driver.db` is generated and updated automatically while using `/aggregate-hours`.
- If `models/model.pkl` is missing, run `src/train.py` first.
