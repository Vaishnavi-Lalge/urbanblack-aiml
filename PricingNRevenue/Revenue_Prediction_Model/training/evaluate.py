"""
IMPROVED MODEL EVALUATION METRICS

Includes:
- Basic regression metrics (MAE, RMSE, R²)
- Percentage error (MAPE)
- Median absolute error
- Custom metrics for business domain
"""

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
import numpy as np


def evaluate_model(y_true, y_pred):
    """
    Evaluate regression model with comprehensive metrics.
    
    Returns:
        dict with MAE, RMSE, R2, MAPE, median_ae, and business metrics
    """
    
    # Basic metrics
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    
    # Percentage metrics
    try:
        mape = float(mean_absolute_percentage_error(y_true, y_pred))
    except:
        mape = -1.0
    
    # Median absolute error
    median_ae = float(np.median(np.abs(y_true - y_pred)))
    
    # Threshold-based metrics (within 10%, 20%, 30%)
    errors = np.abs(y_true - y_pred)
    within_10 = float(np.mean(errors <= 0.1 * y_true))
    within_20 = float(np.mean(errors <= 0.2 * y_true))
    within_30 = float(np.mean(errors <= 0.3 * y_true))
    
    return {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "R2": round(r2, 4),
        "MAPE": round(mape, 4) if mape >= 0 else "N/A",
        "Median_AE": round(median_ae, 2),
        "Within_10pct": round(within_10, 3),
        "Within_20pct": round(within_20, 3),
        "Within_30pct": round(within_30, 3)
    }


def evaluate_residuals(y_true, y_pred):
    """
    Analyze residuals for outliers and bias.
    """
    
    residuals = y_true - y_pred
    
    return {
        "residual_mean": float(np.mean(residuals)),
        "residual_std": float(np.std(residuals)),
        "residual_min": float(np.min(residuals)),
        "residual_max": float(np.max(residuals)),
        "outliers_3std": int(np.sum(np.abs(residuals) > 3 * np.std(residuals)))
    }