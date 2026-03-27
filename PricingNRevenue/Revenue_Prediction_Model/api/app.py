from fastapi import FastAPI
from api.routes.predict import router as predict_router
from datetime import datetime
import pytz

# ✅ Official IST timezone (India incl. Mumbai/Maharashtra)
IST = pytz.timezone("Asia/Kolkata")

app = FastAPI(
    title="Driver Revenue Prediction API",
    version="1.0.0",
    description="ML-powered system for predicting driver revenue and ride demand"
)

# ---------------- ROOT ----------------
@app.get("/")
def root():
    return {
        "status": "success",
        "status_code": 200,
        "message": "🚀 API is running successfully",
        "service": "Driver Revenue Prediction System",
        "region": "Mumbai, Maharashtra, India",  # 👈 you can add this
        "version": app.version,
        "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    }


# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "status_code": 200,
        "service": "healthy",
        "region": "Mumbai, Maharashtra, India",
        "models_loaded": True,
        "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    }


# ---------------- ROUTES ----------------
app.include_router(predict_router)