"""Rate limiting with Redis primary storage and in-memory fallback."""
import time
from collections import defaultdict, deque

import redis
from fastapi import HTTPException

from app.config import settings


class RateLimiter:
    def __init__(self, redis_url: str, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._memory_windows: dict[str, deque] = defaultdict(deque)
        self._redis = None
        if redis_url:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def _check_with_redis(self, bucket: str, now: float) -> None:
        key = f"rate:{bucket}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - self.window_seconds)
        pipe.zcard(key)
        _, current = pipe.execute()

        if int(current) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests} req/min",
                headers={"Retry-After": str(self.window_seconds)},
            )

        member = f"{now:.6f}"
        pipe = self._redis.pipeline()
        pipe.zadd(key, {member: now})
        pipe.expire(key, self.window_seconds * 2)
        pipe.execute()

    def _check_in_memory(self, bucket: str, now: float) -> None:
        window = self._memory_windows[bucket]
        while window and window[0] < now - self.window_seconds:
            window.popleft()
        if len(window) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests} req/min",
                headers={"Retry-After": str(self.window_seconds)},
            )
        window.append(now)

    def check_rate_limit(self, bucket: str) -> None:
        now = time.time()
        if self._redis is not None:
            self._check_with_redis(bucket, now)
            return
        self._check_in_memory(bucket, now)


rate_limiter = RateLimiter(
    redis_url=settings.redis_url,
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
)
