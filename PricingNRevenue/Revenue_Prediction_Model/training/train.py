from preprocessing.preprocess import preprocess_data
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

import joblib
import json
import os
import numpy as np
import pandas as pd

# -------------------------------
# LOAD DATA (REVENUE)
# -------------------------------
X, y_revenue = preprocess_data(target="revenue_per_hour")

# -------------------------------
# LOAD DATA (RIDES)
# -------------------------------
_, y_rides = preprocess_data(target="rides_per_hour")

# -------------------------------
# SPLIT
# -------------------------------
X_train, X_test, y_rev_train, y_rev_test = train_test_split(
    X, y_revenue, test_size=0.2, random_state=42
)

_, _, y_rides_train, y_rides_test = train_test_split(
    X, y_rides, test_size=0.2, random_state=42
)

# -------------------------------
# MODELS FOR REVENUE
# -------------------------------
models = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ),
    "XGBoost": xgb.XGBRegressor(
        n_estimators=500,
        max_depth=8,
        learning_rate=0.03,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_alpha=0.1,
        reg_lambda=1,
        random_state=42
    )
}

# -------------------------------
# TRAIN & SELECT BEST (REVENUE)
# -------------------------------
results = []
best_model = None
best_score = float("inf")
best_model_name = ""

for name, model in models.items():
    print(f"\nTraining {name} (Revenue)...")

    model.fit(X_train, y_rev_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_rev_test, preds)
    rmse = np.sqrt(mean_squared_error(y_rev_test, preds))
    r2 = r2_score(y_rev_test, preds)

    results.append({
        "Model": name,
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2)
    })

    print(f"{name} -> MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.4f}")

    if mae < best_score:
        best_score = mae
        best_model = model
        best_model_name = name

# -------------------------------
# TRAIN RIDES MODEL (XGBOOST)
# -------------------------------
print("\nTraining XGBoost (Rides)...")

rides_model = xgb.XGBRegressor(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42
)

rides_model.fit(X_train, y_rides_train)

rides_preds = rides_model.predict(X_test)

rides_mae = mean_absolute_error(y_rides_test, rides_preds)
rides_r2 = r2_score(y_rides_test, rides_preds)

print(f"Rides Model -> MAE: {rides_mae:.2f}, R2: {rides_r2:.4f}")

# -------------------------------
# SAVE EVERYTHING
# -------------------------------
os.makedirs("model", exist_ok=True)

# Revenue model
joblib.dump(best_model, "model/revenue_model_v1.pkl")

# Rides model
joblib.dump(rides_model, "model/rides_model.pkl")

# Comparison CSV
df = pd.DataFrame(results)
df.to_csv("model/model_comparison.csv", index=False)

# Metrics JSON
metrics = {
    "revenue_model": {
        "model": best_model_name,
        "MAE": float(best_score),
        "RMSE": float(df[df["Model"] == best_model_name]["RMSE"].values[0]),
        "R2": float(df[df["Model"] == best_model_name]["R2"].values[0])
    },
    "rides_model": {
        "model": "XGBoost",
        "MAE": float(rides_mae),
        "R2": float(rides_r2)
    }
}

with open("model/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

# -------------------------------
# FINAL OUTPUT
# -------------------------------
print("\n==============================")
print("REVENUE MODEL COMPARISON:")
print(df)

print("\nBEST REVENUE MODEL:")
print(f"Model: {best_model_name}")
print(f"MAE: {metrics['revenue_model']['MAE']:.2f}")
print(f"R2: {metrics['revenue_model']['R2']:.4f}")

print("\nRIDES MODEL:")
print(f"MAE: {metrics['rides_model']['MAE']:.2f}")
print(f"R2: {metrics['rides_model']['R2']:.4f}")

print("\nModels saved successfully (Revenue + Rides)")