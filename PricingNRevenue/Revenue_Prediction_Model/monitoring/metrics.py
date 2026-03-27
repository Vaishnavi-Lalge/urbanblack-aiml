import json
import os
from datetime import datetime
from utils.logger import get_logger
from config.settings import IST

logger = get_logger(__name__)

LOG_PATH = "monitoring/prediction_logs.json"


def load_logs():
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"❌ Failed to load logs: {str(e)}")
        return []


def save_logs(logs):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

        with open(LOG_PATH, "w") as f:
            json.dump(logs, f, indent=2)

    except Exception as e:
        logger.error(f"❌ Failed to save logs: {str(e)}")


def log_prediction(input_data, prediction_output):
    try:
        logs = load_logs()

        entry = {
            # ✅ IST timestamp
            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
            "input": input_data,
            "output": prediction_output
        }

        logs.append(entry)

        # Optional: limit file size (production safety)
        if len(logs) > 10000:
            logs = logs[-5000:]

        save_logs(logs)

        logger.info("📊 Prediction logged successfully")

    except Exception as e:
        logger.error(f"❌ Logging failed: {str(e)}", exc_info=True)


def compute_metrics():
    try:
        logs = load_logs()

        if not logs:
            return {}

        total_predictions = len(logs)

        revenues = [
            log["output"].get("predicted_revenue", 0)
            for log in logs
        ]

        avg_revenue = sum(revenues) / len(revenues)

        drift_count = sum(
            any(f["drift"] for f in log["output"].get("drift", {}).values())
            for log in logs
        )

        metrics = {
            "total_predictions": total_predictions,
            "avg_revenue": round(avg_revenue, 2),
            "drift_cases": drift_count,
            "last_updated": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        }

        return metrics

    except Exception as e:
        logger.error(f"❌ Metrics computation failed: {str(e)}", exc_info=True)
        return {}