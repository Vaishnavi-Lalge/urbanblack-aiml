from utils.logger import get_logger

logger = get_logger(__name__)


def check_alerts(prediction_output):
    alerts = []

    try:
        revenue = prediction_output.get("predicted_revenue", 0)
        drift_data = prediction_output.get("drift", {})

        # ---------------- LOW REVENUE ALERT ----------------
        if revenue < 100:
            alerts.append("⚠️ Low revenue detected")

        # ---------------- HIGH DRIFT ALERT ----------------
        drift_flags = [v["drift"] for v in drift_data.values()]
        drift_ratio = sum(drift_flags) / (len(drift_flags) + 1e-6)

        if drift_ratio > 0.3:
            alerts.append("🚨 High data drift detected")

        # ---------------- LOG ALERTS ----------------
        for alert in alerts:
            logger.warning(alert)

        return alerts

    except Exception as e:
        logger.error(f"❌ Alert system failed: {str(e)}")
        return []