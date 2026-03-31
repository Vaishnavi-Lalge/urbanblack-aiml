# Urban Black - Dynamic Pricing Engine MVP

This microservice acts as the core mathematical engine to structure, apply, and validate financial and logistical rideshare assignments via FastAPI and LightGBM model inferencing.

## 1. Core Fare Rules & Fees

*   **Distance Charge:** Strictly calculates **₹25 for every kilometer** traveled.
*   **Minimum Ride Fare:** Even for extremely short distances, the **absolute minimum base fare is ₹55**. *(e.g. 1km trip calculates to ₹25, but is forced to the ₹55 minimum).*
*   **Waiting Charges:** Drivers wait for passengers. The **first 5 minutes are fully free**. After that grace period ends, it charges exactly **₹2 per minute**.

## 2. Contextual & Environmental Surcharges

*   **Night Shift Premium:** Any trip made strictly between **10:00 PM (22:00) and 6:00 AM (06:00)** automatically applies a **25% multiplier** on top of the subtotal.
*   **Weather Surcharge:** Sourced from real-time metrics:
    *   **Heavy Rain (> 10.0 mm/hr):** High danger, adds an extra **20%** charge.
    *   **Light/Moderate Rain (> 2.0 mm/hr):** General inconvenience, adds an extra **10%** charge.

## 3. Dynamic Supply & Demand (AI Engine)

*   **LightGBM Real-Time Surge:** A custom-trained machine learning model processes active conditions and maps the zone demand against traffic and historic trip logs.
*   **Surge Caps and Tiers:**
    *   `< 1.2x` = **Normal Demand**
    *   `1.2x to 1.6x` = **Mild Surge**
    *   `1.6x to 2.2x` = **Moderate Surge**
    *   `2.2x to 2.5x` = **Peak Surge**
    *   `> 2.5x` = **CAPPED**. Max allowed legal surge multiplier applied by the engine is 2.5x the fare.
*   *(Rule-Based Fallback)*: If the Machine Learning model is completely disconnected, the engine maps mathematical ratios of available drivers vs active events directly into these same tiers.

## 4. Taxes & Operational Fees

*   **Platform Operations Fee:** The application system incurs a **5% flat fee** applied to the (Fare + Surge). 
*   **GST Taxation:** A strictly mandatory **5% GST** is applied evenly to the entire taxable chunk (Fare + Surge + Platform Fee). 
*   **Toll Exemptions:** Any `toll_cost_estimate` is completely separate and tacked onto the absolute end, escaping GST application as per taxation norms.

## 5. Driver Verification & Shift Logic

The engine explicitly validates whether a driver respects the requirements required for their specific depot/center-point allocation.

*   **Minimum Target Rides:** Driver must complete >= **25 rides**.
*   **Minimum Target Distance:** Driver must actively drive >= **135 km**.
*   **Minimum Target Shift Hours:** Driver must remain actively online >= **12.0 hours**.

## Available Setup & Execution

Run local verification and test via the Swagger Sandbox at `/docs`:
```bash
uvicorn app.main:app --port 8000 --reload
```
