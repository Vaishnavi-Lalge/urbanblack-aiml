import time

# In-memory store (can replace with DB later)
metrics_store = []


def log_prediction(data):
    """
    Log prediction safely (supports revenue + rides)
    """
    try:
        entry = {
            "timestamp": time.time(),
            "input": data.get("input", {}),
            "predicted_revenue": data.get("predicted_revenue", None),
            "predicted_rides": data.get("predicted_rides", None)
        }

        metrics_store.append(entry)

    except Exception as e:
        print("Logging error:", str(e))


def get_metrics():
    """
    Return monitoring statistics
    """
    try:
        total = len(metrics_store)

        avg_revenue = None
        avg_rides = None

        if total > 0:
            revenues = [
                x["predicted_revenue"]
                for x in metrics_store
                if x["predicted_revenue"] is not None
            ]

            rides = [
                x["predicted_rides"]
                for x in metrics_store
                if x["predicted_rides"] is not None
            ]

            if revenues:
                avg_revenue = sum(revenues) / len(revenues)

            if rides:
                avg_rides = sum(rides) / len(rides)

        return {
            "total_predictions": total,
            "avg_revenue": avg_revenue,
            "avg_rides": avg_rides,
            "last_prediction": metrics_store[-1] if total > 0 else None
        }

    except Exception as e:
        return {
            "error": str(e)
        }