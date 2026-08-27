import hashlib
import json
from typing import Any

from redis import Redis


class RedisCache:
    def __init__(self, url: str, ttl_seconds: int = 3600) -> None:
        self.client = Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        self.ttl_seconds = ttl_seconds

    def key(self, endpoint: str, params: dict[str, Any]) -> str:
        encoded = json.dumps(params, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        return f"sports-bi:response:{endpoint.strip('/').replace('/', ':')}:{digest}"

    def get(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]] | None:
        value = self.client.get(self.key(endpoint, params))
        return json.loads(value) if value else None

    def set(self, endpoint: str, params: dict[str, Any], value: list[dict[str, Any]]) -> None:
        self.client.setex(self.key(endpoint, params), self.ttl_seconds, json.dumps(value))

    def consume_quota(self, limit: int, window_seconds: int = 86400) -> bool:
        key = "sports-bi:quota:" + str(self.client.time()[0] // window_seconds)
        count = self.client.incr(key)
        if count == 1:
            self.client.expire(key, window_seconds)
        return count <= limit
