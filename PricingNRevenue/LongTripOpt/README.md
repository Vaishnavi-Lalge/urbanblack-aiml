# LongTripOpt (UrbanBlack) - Execute Model

This folder holds model-related code and data for LongTripOpt pricing/WTA prediction.

## Project layout

- `src/`
  - `load_rides_dataset.py` - load cleaned CSV into PostgreSQL table
  - `fare_calculator.py` - fare model logic (utilized by training/inference pipelines)
  - `extract_pdf.py` - utilities for PDF extraction (if needed)

- `data/`
  - `rides_dataset_clean.csv` - dataset for local development and SQL insert fixtures

- `sql/`
  - `create_rides_table.sql` - schema creation for `rides_dataset`
  - `fare_queries.sql` - read queries for analysis
  - `longtripopt_db_queries.sql` - INSERT sample rows + indexes

- `models/`
  - `model_metadata.json` - model metadata and feature configuration

- `requirements.txt` - python dependencies

## Prerequisites

1. Python 3.10+ installed
2. PostgreSQL 17 (or 14+) installed and accessible
3. Create DB (example):

   ```powershell
   psql -U postgres -c "CREATE DATABASE urbanblack_ride;"
   ```

## Environment setup

```powershell
cd d:\urbanblack-aiml\PricingNRevenue\LongTripOpt
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Initialize DB schema

```powershell
psql -U postgres -d urbanblack_ride -f sql\create_rides_table.sql
```

Optional: Load sample rows in `sql/longtripopt_db_queries.sql`.

```powershell
psql -U postgres -d urbanblack_ride -f sql\longtripopt_db_queries.sql
```

## Load full dataset from CSV

```powershell
python src\load_rides_dataset.py --csv data\rides_dataset_clean.csv --host localhost --port 5432 --dbname urbanblack_ride --user postgres --password root --create-table --table rides_dataset
```

## Evaluate / inference flow

- Use `fare_calculator.py` to compute predicted fare logic (pure feature vectors). 
- In real deployment, this module is integrated into prediction microservice.

## Notes

- Ensure UUIDs in `rides_dataset` are unique and valid.
- If row insert fails due to constraint, delete duplicates and retry macro-load.
- `model_metadata.json` identifies feature groups used for fare/WTA models.

## Execution steps (run + add)

1. Start PostgreSQL and verify:

   ```powershell
   psql -U postgres -d urbanblack_ride -c "SELECT version();"
   ```

2. Create/verify the schema:

   ```powershell
   psql -U postgres -d urbanblack_ride -f sql\create_rides_table.sql
   ```

3. (Optional) Add sample fixture records for quick test:

   ```powershell
   psql -U postgres -d urbanblack_ride -f sql\longtripopt_db_queries.sql
   ```

4. Add production dataset:

   ```powershell
   python src\load_rides_dataset.py --csv data\rides_dataset_clean.csv --host localhost --port 5432 --dbname urbanblack_ride --user postgres --password root --create-table --table rides_dataset
   ```

5. Run and validate row count:

   ```powershell
   psql -U postgres -d urbanblack_ride -c "SELECT COUNT(*) FROM rides_dataset;"
   ```

6. Run fare calculator logic on sample inputs (example):

   ```powershell
   python - <<'PY'
from src.fare_calculator import predict_fare
sample = {
    'actual_distance_km': 10.0,
    'estimated_distance_km': 11.0,
    'approach_km': 2.0,
    'actual_duration_min': 25,
    'estimated_duration_min': 28,
    'trip_type': 'airport',
    'vehicle_type': 'economy',
    'is_peak_hour': True
}
print(predict_fare(sample))
PY
   ```

7. Confirm model metadata and features:

   ```powershell
   cat models\model_metadata.json | ConvertFrom-Json
   ```

8. (Optional) Hit the service endpoint / integration test once API is available.

- Add `--dry-run` to dataset commands for safe test runs if script supports it.
- Keep the DB credentials and paths updated for your environment.

