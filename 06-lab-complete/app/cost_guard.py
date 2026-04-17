"""Cost guard for estimated LLM spend per day."""
from datetime import datetime, timezone

import redis
from fastapi import HTTPException

from app.config import settings


class CostGuard:
    def __init__(self, redis_url: str, daily_budget_usd: float):
        self.daily_budget_usd = daily_budget_usd
        self._redis = None
        self._memory_cost_by_day: dict[str, float] = {}
        if redis_url:
            try:
                self._redis = redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    @staticmethod
    def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
        # gpt-4o-mini reference prices in USD per 1k tokens
        input_cost = (input_tokens / 1000.0) * 0.00015
        output_cost = (output_tokens / 1000.0) * 0.0006
        return input_cost + output_cost

    @staticmethod
    def _day_key(bucket: str) -> str:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"cost:{bucket}:{day}"

    def _get_current_cost(self, key: str) -> float:
        if self._redis is not None:
            return float(self._redis.get(key) or 0.0)
        return float(self._memory_cost_by_day.get(key, 0.0))

    def _set_current_cost(self, key: str, value: float) -> None:
        if self._redis is not None:
            self._redis.set(key, value)
            self._redis.expire(key, 2 * 24 * 3600)
            return
        self._memory_cost_by_day[key] = value

    def check_budget(self, bucket: str, estimated_cost: float) -> None:
        key = self._day_key(bucket)
        current = self._get_current_cost(key)
        if current + estimated_cost > self.daily_budget_usd:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Daily budget exceeded",
                    "used_usd": round(current, 6),
                    "estimated_next_usd": round(estimated_cost, 6),
                    "budget_usd": self.daily_budget_usd,
                },
            )

    def record_usage(self, bucket: str, actual_cost: float) -> float:
        key = self._day_key(bucket)
        current = self._get_current_cost(key)
        updated = current + actual_cost
        self._set_current_cost(key, updated)
        return updated

    def get_daily_cost(self, bucket: str) -> float:
        return self._get_current_cost(self._day_key(bucket))


cost_guard = CostGuard(
    redis_url=settings.redis_url,
    daily_budget_usd=settings.daily_budget_usd,
)
