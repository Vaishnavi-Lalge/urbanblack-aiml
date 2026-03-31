import os
import pytz

# ---------------- BASE DIR ----------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- TIMEZONE ----------------
IST = pytz.timezone("Asia/Kolkata")

# ---------------- DATA PATH ----------------
DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "04_Revenue_Prediction_Model_Requirements.xlsx"
)

# ---------------- MODEL DIR ----------------
MODEL_DIR = os.path.join(BASE_DIR, "model")