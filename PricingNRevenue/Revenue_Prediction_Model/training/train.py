import pandas as pd
import joblib
import json
import os
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from training.config import *
from training.evaluate import evaluate_model


def load_data():
    print("📥 Loading processed data...")
    df = pd.read_csv(DATA_PATH)

    # 🔥 REMOVE NOISE
    df = df[df["fare_amount"] > 0]
    df = df[df["trip_distance"] > 0]
    df = df[df["trip_duration_min"] > 0]

    return df


def prepare_data(df):
    print("🧠 Preparing features and targets...")

    X = df[FEATURE_COLUMNS]

    # 🚀 LOG TRANSFORM (VERY IMPORTANT)
    y_revenue = np.log1p(df[TARGET_REVENUE].clip(lower=50))

    # rides target
    y_rides = df[TARGET_RIDES].clip(lower=1)

    return train_test_split(
        X, y_revenue, y_rides,
        test_size=0.2,
        random_state=42
    )


def train_models(X_train, y_train):
    models = {
        "LinearRegression": LinearRegression(),

        "RandomForest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            random_state=42
        ),

        # 🚀 OPTIMIZED XGBOOST
        "XGBoost": XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=8,
            subsample=0.8,
            colsample_bytree=0.8,
            gamma=1,
            reg_alpha=0.1,
            reg_lambda=1,
            random_state=42
        )
    }

    trained_models = {}

    for name, model in models.items():
        print(f"🚀 Training {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model

    return trained_models


def select_best_model(models, X_test, y_test):
    best_model = None
    best_score = -float("inf")
    best_metrics = {}

    for name, model in models.items():
        preds = model.predict(X_test)
        metrics = evaluate_model(y_test, preds)

        print(f"{name} -> {metrics}")

        if metrics["R2"] > best_score:
            best_score = metrics["R2"]
            best_model = model
            best_metrics = metrics

    return best_model, best_metrics


def save_artifacts(revenue_model, rides_model, metrics):
    print("💾 Saving models...")

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(revenue_model, REVENUE_MODEL_PATH)
    joblib.dump(rides_model, RIDES_MODEL_PATH)

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=4)


def main():
    df = load_data()

    X_train, X_test, y_rev_train, y_rev_test, y_rides_train, y_rides_test = prepare_data(df)

    # Revenue model
    rev_models = train_models(X_train, y_rev_train)
    best_rev_model, rev_metrics = select_best_model(rev_models, X_test, y_rev_test)

    # Rides model
    rides_models = train_models(X_train, y_rides_train)
    best_rides_model, rides_metrics = select_best_model(rides_models, X_test, y_rides_test)

    metrics = {
        "revenue_model": rev_metrics,
        "rides_model": rides_metrics
    }

    save_artifacts(best_rev_model, best_rides_model, metrics)

    print("✅ Training completed!")


if __name__ == "__main__":
    main()