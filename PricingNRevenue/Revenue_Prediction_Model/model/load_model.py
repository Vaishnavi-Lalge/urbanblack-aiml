import os
import joblib
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "model")

REVENUE_MODEL_PATH = os.path.join(MODEL_DIR, "revenue_model.pkl")
RIDES_MODEL_PATH = os.path.join(MODEL_DIR, "rides_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "columns.pkl")

# ---------------- CACHE (LOAD ONCE) ----------------
_revenue_model = None
_rides_model = None
_scaler = None
_columns = None


def load_models():
    global _revenue_model, _rides_model

    if _revenue_model is None or _rides_model is None:
        logger.info("📦 Loading ML models...")

        if not os.path.exists(REVENUE_MODEL_PATH):
            raise FileNotFoundError("❌ revenue_model.pkl not found")

        if not os.path.exists(RIDES_MODEL_PATH):
            raise FileNotFoundError("❌ rides_model.pkl not found")

        _revenue_model = joblib.load(REVENUE_MODEL_PATH)
        _rides_model = joblib.load(RIDES_MODEL_PATH)

        logger.info("✅ Models loaded successfully")

    return _revenue_model, _rides_model


def load_scaler():
    global _scaler

    if _scaler is None:
        logger.info("📦 Loading scaler...")

        if not os.path.exists(SCALER_PATH):
            raise FileNotFoundError("❌ scaler.pkl not found")

        _scaler = joblib.load(SCALER_PATH)

        logger.info("✅ Scaler loaded")

    return _scaler


def load_columns():
    global _columns

    if _columns is None:
        logger.info("📦 Loading feature columns...")

        if not os.path.exists(COLUMNS_PATH):
            raise FileNotFoundError("❌ columns.pkl not found")

        _columns = joblib.load(COLUMNS_PATH)

        logger.info(f"✅ Columns loaded ({len(_columns)} features)")

    return _columns


def validate_model_files():
    required_files = [
        REVENUE_MODEL_PATH,
        RIDES_MODEL_PATH,
        SCALER_PATH,
        COLUMNS_PATH
    ]

    for file in required_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"❌ Missing file: {file}")

    logger.info("✅ All model files validated")