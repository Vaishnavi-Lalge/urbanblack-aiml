import redis
from typing import Optional
import json

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        # We handle exceptions gracefully if Redis isn't running locally yet for MVP
        try:
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis.ping()
        except redis.ConnectionError:
            self.redis = None
            print("Warning: Redis connection failed. Using in-memory dict for mocks.")
            self.mock_store = {}

    def get_zone_state(self, zone_id: str) -> Optional[dict]:
        if self.redis:
            val = self.redis.get(f"zone_state:{zone_id}")
            return json.loads(val) if val else None
        else:
            return self.mock_store.get(f"zone_state:{zone_id}")

    def set_zone_state(self, zone_id: str, state: dict, ttl_seconds: int = 60):
        if self.redis:
            self.redis.setex(f"zone_state:{zone_id}", ttl_seconds, json.dumps(state))
        else:
            self.mock_store[f"zone_state:{zone_id}"] = state

redis_client = RedisClient()
