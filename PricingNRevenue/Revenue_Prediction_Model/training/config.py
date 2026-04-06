"""
IMPROVED TRAINING CONFIGURATION

Uses centralized feature engineering to prevent train/inference mismatch.
"""

import os
from features.feature_definitions import ALL_FEATURES

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data/processed/processed_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

# Model output paths
REVENUE_MODEL_PATH = os.path.join(MODEL_DIR, "revenue_model.pkl")
RIDES_MODEL_PATH = os.path.join(MODEL_DIR, "rides_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

# Feature columns (SINGLE SOURCE OF TRUTH from feature_definitions.py)
FEATURE_COLUMNS = ALL_FEATURES

# Targets
TARGET_REVENUE = "fare_amount"
TARGET_RIDES = "rides_completed_so_far"

# ============================================================================
# TRAINING PARAMETERS
# ============================================================================

# Train/test split
TEST_SIZE = 0.2
VAL_SIZE = 0.1  # Additional validation set
RANDOM_STATE = 42

# XGBoost hyperparameters (tuned for ride-hailing)
XGBOOST_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 8,
    "min_child_weight": 5,  # Prevent overfitting
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "gamma": 1,  # Min loss reduction for split
    "reg_alpha": 0.5,  # L1 regularization
    "reg_lambda": 1.5,  # L2 regularization
    "random_state": RANDOM_STATE,
    "verbosity": 1
}

# RandomForest hyperparameters
RF_PARAMS = {
    "n_estimators": 300,
    "max_depth": 12,
    "min_samples_split": 10,
    "min_samples_leaf": 5,
    "max_features": "sqrt",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
    "verbose": 1
}

# LinearRegression (simple baseline)
LR_PARAMS = {
    "fit_intercept": True
}

# Ridge regression (better with collinearity)
RIDGE_PARAMS = {
    "alpha": 100,  # Regularization strength
    "random_state": RANDOM_STATE
}

# ============================================================================
# DATA CLEANING PARAMETERS
# ============================================================================

# Remove outliers (z-score based)
OUTLIER_THRESHOLD = 3.0  # Standard deviations

# Revenue bounds (validation)
MIN_REVENUE = 25  # INR
MAX_REVENUE = 5000  # INR (sanity check)

# Trip bounds
MIN_DISTANCE = 0.5  # km
MAX_DISTANCE = 200  # km
MIN_DURATION = 1  # minute
MAX_DURATION = 360  # 6 hours

# ============================================================================
# MODEL SELECTION METRICS
# ============================================================================

# Primary metric for model selection
PRIMARY_METRIC = "R2"  # Options: "R2", "MAE", "RMSE", "MAPE"

# Target R²
TARGET_R2 = 0.75

# ============================================================================
# CROSS-VALIDATION
# ============================================================================

N_SPLITS = 5  # 5-fold cross validation

# ============================================================================
# FEATURE SCALING
# ============================================================================

SCALING_METHOD = "StandardScaler"  # or "RobustScaler" for outliers

print(f"✅ Config loaded with {len(FEATURE_COLUMNS)} features")