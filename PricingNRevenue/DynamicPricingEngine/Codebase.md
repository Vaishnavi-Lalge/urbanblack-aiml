# Dynamic Pricing Engine: Codebase & Architecture Overview

This document walks through every active code file in the current directory and explains exactly what it does, why it is required, and how it fits into the microservice architecture.

---

## 🚀 1. Core Application Entry

### `app/main.py`
*   **What it does:** This is the entry point of the entire FastAPI application. It creates the app, defines the titles/metadata, and mounts the available API routers (`/pricing` and `/driver`).
*   **Why it's required:** Without this file, the web server (Uvicorn) wouldn't know where to start or which endpoints exist.

---

## 🕸️ 2. API Endpoints (Routing)

### `app/api/endpoints/pricing.py`
*   **What it does:** Exposes the HTTP POST endpoint `/api/v1/pricing/compute-fare`. It takes in the JSON request, sends it to the calculator, and returns the response.
*   **Why it's required:** Acts as the bridge between the outside internet (mobile apps, other servers) and our internal math logic.

### `app/api/endpoints/driver.py`
*   **What it does:** Exposes the HTTP POST endpoint `/api/v1/driver/shift-status`. It receives the driver's current shift data and immediately returns whether they passed or failed the shift requirements.
*   **Why it's required:** Allows external services (like the Driver App) to actively ask if a driver has hit their targets (25 rides / 12 hours / 135 km) for the day.

---

## 🧠 3. Services (The Heavy Lifting / Logic)

### `app/services/pricing_calculator.py`
*   **What it does:** The absolute core of the engine. It calculates the flat base fare (₹55 min), the ₹25 distance additions, the ₹2 waiting fees, applies the 25% night and 10-20% weather surcharges, forces the 5% GST & Platform taxes, and applies the ML surge multiplier.
*   **Why it's required:** Encapsulates the actual business logic so the API endpoints stay totally clean and focused only on web traffic.

### `app/services/ml_surge_predictor.py`
*   **What it does:** Loads the trained `LightGBM` AI model from disk into memory. It takes the live traffic and weather numbers, feeds them into the model, and outputs a dynamic `surge_multiplier` (between 1.0x and 2.5x).
*   **Why it's required:** This connects the static web app to the dynamic intelligence of the AI model.

### `app/services/rule_based_surge.py`
*   **What it does:** A hardcoded rule dictionary that decides surge multipliers directly based on `zone_demand_supply_ratio` (Active Users vs Available Cabs).
*   **Why it's required:** This is our **Fallback / Cold-Start** system. If the AI model crashes or is deleted, this script takes over and ensures the company is still dynamically charging based on supply and demand.

### `app/services/driver_shift_tracker.py`
*   **What it does:** Contains the mathematical logic to subtract a driver's completed data from the target requirements (25 rides, 12 hours, 135 km). 
*   **Why it's required:** Separate from the pricing calculator, this strictly handles the logic to tell us if a driver shift is failing, and specifically by how much (e.g. "needs 2 more rides to pass").

---

## 📦 4. Data Models (Validation)

### `app/models/schemas.py`
*   **What it does:** Defines exact formats (`PricingRequest`, `PricingResponse`) using Pydantic. If someone tries to send a string when a number is expected, this intercepts it and throws a 422 Error automatically.
*   **Why it's required:** Ensures all JSON payloads strictly follow the rules. This prevents our calculators from crashing due to bad input data.

### `app/models/driver_schemas.py`
*   **What it does:** Defines the input format (`DriverShiftMetrics`) needed to validate a driver. It enforces that variables like `min_rides_required: 25` exist properly.
*   **Why it's required:** Standardizes the shift evaluation APIs.

---

## ⚙️ 5. External Core Integrations

### `app/core/kafka_producer.py`
*   **What it does:** A stub class meant to stream all completed pricing evaluations into an asynchronous Kafka broker. 
*   **Why it's required:** Crucial in an enterprise architecture for data engineering! Every fare predicted will be published here so other services (like accounting or analytics) can consume them in real-time.

### `app/core/redis_client.py`
*   **What it does:** An asynchronous caching system meant to temporarily store and fetch high-volume fast-paced data (e.g., retrieving active riders in a zone).
*   **Why it's required:** Hitting a main backend Database for every single surge calculation would crash it. Redis allows ultra-fast data retrieval for the endpoints.

---

## 🧪 6. Machine Learning & Testing Scripts

### `ml/train.py`
*   **What it does:** Uses `pandas` to open the `utr_fare_dataset_7500.csv` dataset, cleans the anomalies, maps rainfall text to numeric values, creates proxy demand variables, trains the `LightGBM` model for 500 rounds, and then saves it as `models/surge_lgb_model.txt`.
*   **Why it's required:** This is exactly how the AI model learns from real-world datasets rather than guessing numbers. 

### `test_pricing.py`
*   **What it does:** A tiny, isolated script used to mock a single PricingRequest straight into the python calculator script without needing to launch a web server.
*   **Why it's required:** A fast and effective way to instantly locally test if math alterations break the output structure or results without going into the Swagger UI.
