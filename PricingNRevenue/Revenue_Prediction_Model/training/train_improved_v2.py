"""
IMPROVED TRAINING - Production Ready

Key Improvements:
1. Train rides model on rides_per_hour (not cumulative rides)
2. Better hyperparameter tuning
3. Separate optimized models for revenue vs rides
4. Proper cross-validation
5. Overfitting prevention with regularization
"""

import pandas as pd
import numpy as np
import joblib
import json
import os
from pathlib import Path

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from preprocessing.preprocess_improved import preprocess_data
from training.evaluate import evaluate_model


class ImprovedTrainer:
    """Production-grade ML trainer for ride-hailing predictions."""
    
    def __init__(self, data_path="data/processed/processed_data.csv", model_dir="model"):
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
    def load_and_prepare_data(self):
        """Load and prepare data with rides_per_hour target."""
        print("📥 Loading data...")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        # Validate required columns
        if "rides_per_hour" not in df.columns:
            raise ValueError("❌ rides_per_hour not found! Run preprocess_improved.py first")
        
        # Feature columns (must match preprocessing)
        FEATURE_COLUMNS = [
            "hour_of_day", "is_peak_hour", "is_night_trip", "is_morning_peak",
            "is_lunch_rush", "is_evening_peak", "is_late_night",
            "trip_distance", "trip_duration_min", "avg_speed", "ride_efficiency",
            "is_short_trip", "is_long_trip",
            "driver_rating", "driver_total_trips", "driver_shift_hours_elapsed",
            "is_new_driver", "is_experienced_driver", "high_rated_driver", "low_rated_driver",
            "shift_progress_percent",
            "number_of_rides_in_zone", "number_of_active_drivers_in_zone",
            "demand_supply_ratio", "low_supply", "high_demand", "demand_intensity",
            "surge_multiplier", "zone_surge_multiplier", "weather_surge_multiplier",
            "total_op_km_today", "extra_km", "km_milestone_100", "km_milestone_150",
            "km_milestone_200", "extra_bonus", "rides_per_hour"
        ]
        
        # Verify all features exist
        missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"❌ Missing features: {missing}")
        
        X = df[FEATURE_COLUMNS]
        
        # ===== TARGETS =====
        # Revenue target (with log transform for stability)
        y_revenue = np.log1p(df["fare_amount"].clip(lower=25, upper=5000))
        
        # Rides target (rides_per_hour - normalized)
        y_rides = df["rides_per_hour"].clip(lower=0.1, upper=4.0)
        
        print(f"✅ Data loaded: {X.shape}")
        print(f"   Revenue (log): {y_revenue.describe()}")
        print(f"   Rides/hour: {y_rides.describe()}")
        
        return X, y_revenue, y_rides, FEATURE_COLUMNS
    
    def split_data(self, X, y_revenue, y_rides, test_size=0.2, val_size=0.1):
        """Split data into train/validation/test."""
        print("\n✂️ Splitting data...")
        
        # First split: train+val vs test
        X_temp, X_test, y_rev_temp, y_rev_test, y_rid_temp, y_rid_test = train_test_split(
            X, y_revenue, y_rides,
            test_size=test_size,
            random_state=42
        )
        
        # Second split: train vs val
        val_size_adjusted = val_size / (1 - test_size)
        X_train, X_val, y_rev_train, y_rev_val, y_rid_train, y_rid_val = train_test_split(
            X_temp, y_rev_temp, y_rid_temp,
            test_size=val_size_adjusted,
            random_state=42
        )
        
        print(f"   Train: {X_train.shape}")
        print(f"   Validation: {X_val.shape}")
        print(f"   Test: {X_test.shape}")
        
        return (X_train, X_val, X_test), (y_rev_train, y_rev_val, y_rev_test), (y_rid_train, y_rid_val, y_rid_test)
    
    def build_revenue_models(self):
        """Revenue prediction models."""
        return {
            "LinearRegression": LinearRegression(),
            
            "Ridge": Ridge(alpha=100, random_state=42),
            
            "RandomForest": RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=3,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
                verbose=0
            ),
            
            "XGBoost": XGBRegressor(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                min_child_weight=5,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=1,
                reg_alpha=0.5,
                reg_lambda=1.5,
                random_state=42,
                verbosity=0
            )
        }
    
    def build_rides_models(self):
        """Rides prediction models (for rides_per_hour)."""
        return {
            "LinearRegression": LinearRegression(),
            
            "Ridge": Ridge(alpha=50, random_state=42),
            
            "RandomForest": RandomForestRegressor(
                n_estimators=150,
                max_depth=8,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
                verbose=0
            ),
            
            "XGBoost": XGBRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=5,
                min_child_weight=3,
                subsample=0.9,
                colsample_bytree=0.9,
                gamma=0.5,
                reg_alpha=0.1,
                reg_lambda=0.5,
                random_state=42,
                verbosity=0
            )
        }
    
    def train_models(self, X_train, y_train, model_dict, model_type="revenue"):
        """Train multiple models and return them."""
        print(f"\n🚀 Training {model_type} models...")
        
        trained_models = {}
        
        for name, model in model_dict.items():
            print(f"   Training {name}...", end=" ", flush=True)
            
            # Train
            model.fit(X_train, y_train)
            trained_models[name] = model
            
            # CV score
            cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring="r2")
            print(f"CV R²: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")
        
        return trained_models
    
    def select_best_model(self, models, X_test, y_test, model_type="revenue"):
        """Select best model based on test performance."""
        print(f"\n🏆 Evaluating {model_type} models...")
        
        best_model = None
        best_name = None
        best_score = -float("inf")
        best_metrics = {}
        
        results = {}
        
        for name, model in models.items():
            preds = model.predict(X_test)
            metrics = evaluate_model(y_test, preds)
            results[name] = metrics
            
            print(f"   {name:15} → R²: {metrics['R2']:.3f}, MAE: {metrics['MAE']:.3f}, MAPE: {metrics['MAPE']:.1f}%")
            
            if metrics['R2'] > best_score:
                best_score = metrics['R2']
                best_model = model
                best_name = name
                best_metrics = metrics
        
        print(f"\n✅ Best model: {best_name} (R²: {best_metrics['R2']:.3f})")
        
        return best_model, best_name, best_metrics, results
    
    def train_and_evaluate(self):
        """Full training pipeline."""
        print("\n" + "="*70)
        print("🚀 IMPROVED TRAINING PIPELINE")
        print("="*70)
        
        # ===== DATA PREPARATION =====
        X, y_revenue, y_rides, features = self.load_and_prepare_data()
        X_splits, y_rev_splits, y_rid_splits = self.split_data(X, y_revenue, y_rides)
        X_train, X_val, X_test = X_splits
        y_rev_train, y_rev_val, y_rev_test = y_rev_splits
        y_rid_train, y_rid_val, y_rid_test = y_rid_splits
        
        # ===== TRAIN REVENUE MODEL =====
        revenue_models = self.build_revenue_models()
        trained_revenue = self.train_models(X_train, y_rev_train, revenue_models, "revenue")
        revenue_model, revenue_name, revenue_metrics, revenue_results = \
            self.select_best_model(trained_revenue, X_test, y_rev_test, "revenue")
        
        # ===== TRAIN RIDES MODEL (KEY IMPROVEMENT!) =====
        rides_models = self.build_rides_models()
        trained_rides = self.train_models(X_train, y_rid_train, rides_models, "rides_per_hour")
        rides_model, rides_name, rides_metrics, rides_results = \
            self.select_best_model(trained_rides, X_test, y_rid_test, "rides_per_hour")
        
        # ===== SAVE MODELS =====
        print("\n💾 Saving models...")
        joblib.dump(revenue_model, self.model_dir / "revenue_model.pkl")
        joblib.dump(rides_model, self.model_dir / "rides_model.pkl")
        joblib.dump(features, self.model_dir / "columns.pkl")
        
        # Scaler
        scaler = StandardScaler()
        scaler.fit(X_train)
        joblib.dump(scaler, self.model_dir / "scaler.pkl")
        
        print(f"   ✅ Models saved to {self.model_dir}/")
        
        # ===== SAVE METRICS =====
        metrics = {
            "revenue_model": {
                "name": revenue_name,
                "R2": float(revenue_metrics["R2"]),
                "MAE": float(revenue_metrics["MAE"]),
                "RMSE": float(revenue_metrics["RMSE"]),
                "MAPE": float(revenue_metrics["MAPE"]),
                "all_results": {k: float(v["R2"]) for k, v in revenue_results.items()}
            },
            "rides_model": {
                "name": rides_name,
                "R2": float(rides_metrics["R2"]),
                "MAE": float(rides_metrics["MAE"]),
                "RMSE": float(rides_metrics["RMSE"]),
                "MAPE": float(rides_metrics["MAPE"]),
                "all_results": {k: float(v["R2"]) for k, v in rides_results.items()}
            },
            "data": {
                "n_features": len(features),
                "train_size": len(X_train),
                "val_size": len(X_val),
                "test_size": len(X_test),
                "features": features
            }
        }
        
        with open(self.model_dir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        
        print(f"   ✅ Metrics saved")
        
        # ===== RESULTS SUMMARY =====
        print("\n" + "="*70)
        print("📊 TRAINING COMPLETE")
        print("="*70)
        print(f"\n🏆 Revenue Model: {revenue_name}")
        print(f"   R²: {revenue_metrics['R2']:.3f}")
        print(f"   MAE: ₹{revenue_metrics['MAE']:.2f}")
        print(f"   RMSE: ₹{revenue_metrics['RMSE']:.2f}")
        
        print(f"\n🏆 Rides Model (rides_per_hour): {rides_name}")
        print(f"   R²: {rides_metrics['R2']:.3f}")
        print(f"   MAE: {rides_metrics['MAE']:.3f} rides/hour")
        print(f"   RMSE: {rides_metrics['RMSE']:.3f} rides/hour")
        
        print(f"\n📁 Models saved to: {self.model_dir}/")
        print("="*70 + "\n")
        
        return revenue_model, rides_model, metrics


if __name__ == "__main__":
    # Run improved training
    trainer = ImprovedTrainer()
    revenue_model, rides_model, metrics = trainer.train_and_evaluate()
    print("✅ Training pipeline complete!")

