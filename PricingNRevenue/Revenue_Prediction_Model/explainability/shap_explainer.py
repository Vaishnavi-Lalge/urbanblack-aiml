import shap
import joblib
import os
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "revenue_model.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")

# Load once (IMPORTANT)
model = joblib.load(MODEL_PATH)
feature_names = joblib.load(COLUMNS_PATH)

# Create SHAP explainer
explainer = shap.Explainer(model)


def get_shap_explanation(X_scaled, top_k=5):
    try:
        # Compute SHAP values
        shap_values = explainer(X_scaled)

        values = shap_values.values[0]

        # Map features with importance
        feature_impact = list(zip(feature_names, values))

        # Sort by absolute impact
        feature_impact.sort(key=lambda x: abs(x[1]), reverse=True)

        # Take top features
        top_features = feature_impact[:top_k]

        # Format output
        explanation = [
            {
                "feature": feature,
                "impact": float(round(impact, 4))
            }
            for feature, impact in top_features
        ]

        return explanation

    except Exception as e:
        logger.error(f"❌ SHAP explanation failed: {str(e)}")
        return []