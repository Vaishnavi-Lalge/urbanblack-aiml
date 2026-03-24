import joblib
import os

def load_models():
    """
    Load both revenue and rides models
    """
    revenue_model_path = os.path.join("model", "revenue_model_v1.pkl")
    rides_model_path = os.path.join("model", "rides_model.pkl")

    revenue_model = joblib.load(revenue_model_path)
    rides_model = joblib.load(rides_model_path)

    return revenue_model, rides_model