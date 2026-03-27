# Urban Black - Dynamic Pricing Engine MVP

This repository contains the Dynamic Pricing Engine microservice designed for Urban Black. The engine computes real-time optimal surge pricing algorithms leveraging machine learning, while providing fallback rule-based matrices.

## Key Features & Rules Implemented

1. **Explicit Fare Structures**:
    *   Base Fare: ₹55 for the first 1.5 km.
    *   Distance Charge: ₹25 per additional km.
    *   Waiting Charge: First 5 minutes free, then ₹2 per minute.
    *   Taxes & Fees: Configurable Platform Fee + 5% GST strictly applied.

2. **Contextual Modifiers (Rule-Based & ML)**:
    *   **Night Surcharge**: 25% extra for rides between 10 PM and 6 AM.
    *   **Weather Surcharge**: 10-20% modifier depending on `rainfall_mm_per_hour`.
    *   **Dynamic Demand Surge**: We utilize a trained LightGBM model stored in `/models` that outputs dynamic tier (Normal, Mild, Moderate, Peak, Capped) based on demand-supply ratios.

3. **Driver Shift Validation**:
    *   The service contains logic tracking whether drivers meet strict allocation criteria.
    *   Constraints tracked: Minimum 25 rides, Minimum 12 hours, Minimum 135 km distance.

## Architecture

* **Framework**: FastAPI (async HTTP parsing and validations with Pydantic)
* **ML Layer**: LightGBM (Regression modeling over supply/demand multipliers)
* **Data Sources**: Model successfully retrained with the provided realistic trip log dataset, `utr_fare_dataset_7500.csv`.

## API Endpoints

* `POST /api/v1/pricing/compute-fare` 
  Computes the fare breakdown for an incoming ride request and applies dynamic surge.
* `POST /api/v1/driver/shift-status`
  Verifies whether a driver's ongoing shift metrics fulfill exactly the constraints required for their depot/center-point allocation.

## Testing & Deployment

Run local verification via:
```bash
python test_pricing.py
```
