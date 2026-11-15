import json
import logging
import math
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("anomaly_detector")


class TTLCache:
    def __init__(self, ttl_seconds: int = 30):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds debe ser mayor que cero")

        self.ttl_seconds = ttl_seconds
        self._data = {}
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None

            expires_at, value = item
            if time.monotonic() >= expires_at:
                self._data.pop(key, None)
                return None

            return value

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = (
                time.monotonic() + self.ttl_seconds,
                value,
            )

    def clear(self):
        with self._lock:
            self._data.clear()


class DashboardCache:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._memory = TTLCache(ttl_seconds)
        self._redis = None
        self.backend = "memory"

    async def connect(self, redis_url: str | None = None):
        if not redis_url:
            self.backend = "memory"
            logger.info("dashboard_cache_backend=memory")
            return

        try:
            from redis.asyncio import Redis

            client = Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                health_check_interval=30,
            )
            await client.ping()
            self._redis = client
            self.backend = "redis"
            logger.info("dashboard_cache_backend=redis")
        except Exception as exc:
            self._redis = None
            self.backend = "memory"
            logger.warning(
                "redis_cache_unavailable error_type=%s fallback=memory",
                type(exc).__name__,
            )

    async def get(self, key: str):
        if self._redis is not None:
            try:
                raw_value = await self._redis.get(key)
                if raw_value is not None:
                    return json.loads(raw_value)
            except Exception as exc:
                logger.warning(
                    "redis_cache_read_failed error_type=%s fallback=memory",
                    type(exc).__name__,
                )
                await self._disable_redis()

        return self._memory.get(key)

    async def set(self, key: str, value):
        self._memory.set(key, value)

        if self._redis is not None:
            try:
                await self._redis.set(
                    key,
                    json.dumps(value, ensure_ascii=False),
                    ex=self.ttl_seconds,
                )
            except Exception as exc:
                logger.warning(
                    "redis_cache_write_failed error_type=%s fallback=memory",
                    type(exc).__name__,
                )
                await self._disable_redis()

    async def clear(self, key: str | None = None):
        if key is None:
            self._memory.clear()
        else:
            with self._memory._lock:
                self._memory._data.pop(key, None)

        if self._redis is not None:
            try:
                if key is None:
                    await self._redis.flushdb()
                else:
                    await self._redis.delete(key)
            except Exception as exc:
                logger.warning(
                    "redis_cache_clear_failed error_type=%s",
                    type(exc).__name__,
                )
                await self._disable_redis()

    async def _disable_redis(self):
        client = self._redis
        self._redis = None
        self.backend = "memory"

        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass

    async def close(self):
        if self._redis is not None:
            client = self._redis
            self._redis = None
            try:
                await client.aclose()
            except Exception as exc:
                logger.warning(
                    "redis_cache_close_failed error_type=%s",
                    type(exc).__name__,
                )

    def status(self):
        return {
            "backend": self.backend,
            "fallback_available": True,
        }


class Metrics:
    LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

    def __init__(self):
        self._lock = Lock()
        self._started_monotonic = time.monotonic()
        self._started_at = datetime.now(timezone.utc)
        self.requests_total = 0
        self.errors_total = 0
        self.total_latency_seconds = 0.0
        self.max_latency_seconds = 0.0
        self.by_status = defaultdict(int)
        self.by_method = defaultdict(int)
        self.by_path = defaultdict(int)
        self.latency_buckets = {
            str(bound): 0 for bound in self.LATENCY_BUCKETS
        }
        self.latency_buckets["+Inf"] = 0
        self._recent_requests = deque()

    def _prune_recent(self, now: float):
        cutoff = now - 900
        while self._recent_requests and self._recent_requests[0][0] < cutoff:
            self._recent_requests.popleft()

    def record(
        self,
        method: str,
        status_code: int,
        latency_seconds: float,
        path: str = "unknown",
    ):
        now = time.monotonic()
        latency = max(0.0, float(latency_seconds))
        status = int(status_code)
        method_name = str(method).upper()
        path_name = str(path)[:160]

        with self._lock:
            self.requests_total += 1
            self.total_latency_seconds += latency
            self.max_latency_seconds = max(
                self.max_latency_seconds,
                latency,
            )
            self.by_status[str(status)] += 1
            self.by_method[method_name] += 1
            self.by_path[path_name] += 1

            for bound in self.LATENCY_BUCKETS:
                if latency <= bound:
                    self.latency_buckets[str(bound)] += 1
            self.latency_buckets["+Inf"] += 1

            self._recent_requests.append(
                (now, status, method_name, path_name, latency)
            )
            self._prune_recent(now)

    def snapshot(self):
        now = time.monotonic()

        with self._lock:
            self._prune_recent(now)

            average_latency = (
                self.total_latency_seconds / self.requests_total
                if self.requests_total
                else 0.0
            )

            target = math.ceil(self.requests_total * 0.95)
            p95_latency = None

            if target:
                for bound in self.LATENCY_BUCKETS:
                    if self.latency_buckets[str(bound)] >= target:
                        p95_latency = bound * 1000
                        break

            recent_5m = [
                item for item in self._recent_requests
                if item[0] >= now - 300
            ]
            recent_15m = list(self._recent_requests)

            minute_counts = defaultdict(lambda: {"requests": 0, "errors": 0})
            for timestamp, status, _method, _path, _latency in recent_15m:
                minute_key = int(timestamp // 60) * 60
                minute_counts[minute_key]["requests"] += 1
                if status >= 400:
                    minute_counts[minute_key]["errors"] += 1

            current_minute = int(now // 60) * 60
            requests_by_minute = []

            for offset in range(14, -1, -1):
                minute = current_minute - (offset * 60)
                counts = minute_counts[minute]
                requests_by_minute.append({
                    "timestamp": datetime.fromtimestamp(
                        minute,
                        timezone.utc,
                    ).isoformat(),
                    "requests": counts["requests"],
                    "errors": counts["errors"],
                })

            errors_last_5m = sum(
                1 for item in recent_5m if item[1] >= 400
            )
            requests_by_path = sorted(
                self.by_path.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:10]

            uptime_seconds = max(
                0.0,
                now - self._started_monotonic,
            )

            return {
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "error_rate_percent": round(
                    (self.errors_total / self.requests_total) * 100,
                    2,
                ) if self.requests_total else 0.0,
                "average_latency_ms": round(
                    average_latency * 1000,
                    3,
                ),
                "p95_latency_ms": round(p95_latency, 3)
                if p95_latency is not None else None,
                "max_latency_ms": round(
                    self.max_latency_seconds * 1000,
                    3,
                ),
                "requests_last_5m": len(recent_5m),
                "errors_last_5m": errors_last_5m,
                "requests_per_minute_5m": round(
                    len(recent_5m) / 5,
                    2,
                ),
                "requests_last_15m": len(recent_15m),
                "uptime_seconds": round(uptime_seconds, 1),
                "started_at": self._started_at.isoformat(),
                "requests_by_status": dict(self.by_status),
                "requests_by_method": dict(self.by_method),
                "requests_by_path": [
                    {"path": path, "count": count}
                    for path, count in requests_by_path
                ],
                "requests_by_minute": requests_by_minute,
                "latency_buckets": [
                    {
                        "le_seconds": bound,
                        "count": self.latency_buckets[str(bound)],
                    }
                    for bound in self.LATENCY_BUCKETS
                ] + [{
                    "le_seconds": None,
                    "count": self.latency_buckets["+Inf"],
                }],
                "scope": "Proceso actual; los contadores se reinician al reiniciar la aplicacion.",
            }


metrics = Metrics()
dashboard_cache = DashboardCache(ttl_seconds=30)


def should_track_request(path: str) -> bool:
    excluded_paths = {
        "/health",
        "/health/db",
        "/metrics",
        "/dashboard/usage",
    }

    if path in excluded_paths:
        return False

    return not path.startswith("/static/")
