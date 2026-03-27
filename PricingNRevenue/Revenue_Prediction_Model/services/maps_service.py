import os
import json
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

CACHE_PATH = "data/external/maps_cache.json"


# ---------------- CACHE FUNCTIONS ----------------
def load_cache():
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Cache load failed: {str(e)}")

    return {}


def save_cache(cache):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"⚠️ Cache save failed: {str(e)}")


# ---------------- MAIN FUNCTION ----------------
def get_distance_duration(origin_lat, origin_lng, dest_lat, dest_lng):
    try:
        # -------- API KEY CHECK --------
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError("❌ GOOGLE_MAPS_API_KEY not set in .env")

        # -------- CACHE CHECK --------
        cache = load_cache()
        cache_key = f"{origin_lat},{origin_lng}_{dest_lat},{dest_lng}"

        if cache_key in cache:
            logger.info("⚡ Cache hit for maps API")
            return cache[cache_key]

        # -------- API REQUEST --------
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"

        params = {
            "origins": f"{origin_lat},{origin_lng}",
            "destinations": f"{dest_lat},{dest_lng}",
            "key": GOOGLE_MAPS_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code != 200:
            raise Exception(f"HTTP Error: {response.status_code}")

        data = response.json()

        if data.get("status") != "OK":
            raise Exception(f"API Error: {data.get('status')}")

        element = data["rows"][0]["elements"][0]

        if element.get("status") != "OK":
            raise Exception(f"Element Error: {element.get('status')}")

        # -------- EXTRACT DATA --------
        distance_km = element["distance"]["value"] / 1000
        duration_min = element["duration"]["value"] / 60

        result = {
            "distance_km": round(distance_km, 2),
            "duration_min": round(duration_min, 2)
        }

        # -------- SAVE CACHE --------
        cache[cache_key] = result
        save_cache(cache)

        logger.info(f"📍 Distance: {distance_km} km, Duration: {duration_min} min")

        return result

    except Exception as e:
        logger.error(f"❌ Maps API failed: {str(e)}")

        # -------- FALLBACK --------
        return {
            "distance_km": 5.0,
            "duration_min": 15.0
        }